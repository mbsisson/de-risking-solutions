import time
import torch
import numpy as np
from myutils import myshownparraythresh, breakexit


def constructmodel(softmaxdata):
    alpha = softmaxdata['alpha']

    # Pre-group features by sense
    grouped = {'>': [], '<': [], '=': []}
    for feati in softmaxdata['features']:
        grouped[feati['sense']].append(feati)

    def preprocess_group(feats, device):
        A = torch.stack([f['riskyexpr'] for f in feats]).to(device)
        slack = torch.tensor([f['slack'] for f in feats], device=device)
        scale = torch.tensor([f['scale'] for f in feats], device=device)
        return A, slack, scale

    # Precompute tensors
    tensors = {}
    for sense, feats in grouped.items():
        if feats:
            tensors[sense] = preprocess_group(feats, "cpu")  # device should match z

    def logsumexp(z):
        violations = []

        if '>' in tensors:
            A, slack, scale = tensors['>']
            violations.append(torch.relu(-A @ z - slack) / scale)

        if '<' in tensors:
            A, slack, scale = tensors['<']
            violations.append(torch.relu(slack - A @ z) / scale)

        if '=' in tensors:
            A, _, scale = tensors['=']
            violations.append(torch.abs(A @ z) / scale)

        violations = torch.cat(violations, dim=0)
        #print("violations:", violations)
        return torch.logsumexp(alpha * violations, dim=0)

    return logsumexp


def drsk_softmax(alldata, loud=False):
    log = alldata['log']
    log.joint('Running Red gradient ascent for SOFTMAX-ADVERSARIAL\n')

    softmaxdata = alldata['softmax']
    log.joint('zdim = %d\n'%softmaxdata['zdim'])

    z = softmaxdata['z'] = None

    # Define model
    model = constructmodel(softmaxdata)  # TODO should be done outside loop?
    objective_to_minimize = lambda z: -model(z)

    log.joint("START: Running PyTorch FOM...\n")
    start_time = time.time()

    n_rounds = 0
    n_iters = 1000

    # PHASE 1: find a penalty parameter value that gives a feasible solution
    penalty_param = 0.1
    penalty_param_prev = 0.0
    done = False
    while not done:

        # Construct iterate
        z = torch.normal(mean=0.0, std=0.0001, size=(softmaxdata['zdim'],)).requires_grad_()
        z_original = z.detach().clone()  #store original

        # Define optimizer
        optimizer = torch.optim.Adam([z], lr=1e-3)

        # Run gradient descent (really ascent)
        n_rounds += 1
        gradientconverged = False
        log.joint("  Running gradient ascent with penalty param %f\n"%penalty_param)
        for it in range(n_iters):
            ## Clear accumulation of gradients from previous steps
            optimizer.zero_grad()
        
            ## Compute loss function
            logsumexp_potential = objective_to_minimize(z)
            penalty = torch.norm(z, 2) ** 2
            loss = logsumexp_potential + penalty_param * penalty
            
            ## Compute gradient of loss function w.r.t. all parameters in optimizer
            loss.backward()
            #print("gradient=", z.grad)
            
            ## Convergence check
            grad_norm = torch.norm(z.grad, 2)
            if grad_norm < 1e-5:
                gradientconverged = True
                break

            old_z = z.detach().clone()

            ## Take a step of the optimizer against the gradient to minimize against loss
            optimizer.step()

            step_norm = torch.norm(z.detach() - old_z, 2)

            print(
                f"iter {it:4d}: "
                f"loss={loss.item():.6e}, "
                f"grad={grad_norm.item():.6e}, "
                f"step={step_norm.item():.6e}"
            )

        log.joint("   >finished in %d steps\n"%(it+1))

        # Compare final solution to original
        z_change = z.detach() - z_original
        absolute_change = torch.norm(z_change, 2)
        original_norm = torch.norm(z_original, 2)
        relative_change = absolute_change / (original_norm + 1e-12)
        log.joint(f"    Original ||z||:   {original_norm.item():.6e}\n")
        log.joint(f"    Change ||dz||:    {absolute_change.item():.6e}\n")
        log.joint(f"    Relative change:  {relative_change.item():.6e}\n")
        log.joint(f"    Max |dz_i|:       {torch.max(torch.abs(z_change)).item():.6e}\n")

        # Check if solution satisfies budget constraints
        norm = torch.norm(z.detach(), 2)
        if norm <= softmaxdata['budget']:
            log.joint("  penalty parameter: {} gives solution satisfying budget constraint, norm = {}\n".format(penalty_param, norm))
            done = True
        else:
            # Increase penalty param
            log.joint("  penalty parameter: {} too small, norm = {}\n".format(penalty_param, norm))
            penalty_param_prev = penalty_param
            penalty_param *= 2

        breakexit("step")

    # PHASE 2: ensure penalty parameter gives solution that uses enough budget
    budget_threshold = 0.1 * softmaxdata['budget']
    interval_threshold = 1e-3
    pLeft = penalty_param_prev
    pRight = penalty_param
    done = False
    while not done:
        penalty_param = pLeft + (pRight - pLeft) / 2.0

        # Construct iterate
        z = torch.normal(mean=0.0, std=0.0001, size=(softmaxdata['zdim'],)).requires_grad_()
        z_original = z.detach().clone()  #store original

        # Define optimizer
        optimizer = torch.optim.Adam([z], lr=1e-1)

        # Run gradient descent
        n_rounds += 1
        gradientconverged = False
        log.joint("  Running gradient ascent with penalty param %f\n"%penalty_param)
        for it in range(2*n_iters):
            ## Clear accumulation of gradients from previous steps
            optimizer.zero_grad()
        
            ## Compute loss function
            logsumexp_potential = objective_to_minimize(z)
            penalty = torch.norm(z, 2) ** 2
            loss = logsumexp_potential + penalty_param * penalty
            
            ## Compute gradient of loss function w.r.t. all parameters in optimizer
            loss.backward()
            #print("gradient=", z.grad)

            ## Convergence check
            if torch.norm(z.grad, 2) < 1e-5:
                gradientconverged = True
                break
            
            ## Take a step of the optimizer against the gradient to minimize against loss
            optimizer.step()

        log.joint("   >finished in %d steps\n"%(it+1))

        # Compare final solution to original
        z_change = z.detach() - z_original
        absolute_change = torch.norm(z_change, 2)
        original_norm = torch.norm(z_original, 2)
        relative_change = absolute_change / (original_norm + 1e-12)
        log.joint(f"    Original ||z||:   {original_norm.item():.6e}\n")
        log.joint(f"    Change ||dz||:    {absolute_change.item():.6e}\n")
        log.joint(f"    Relative change:  {relative_change.item():.6e}\n")
        log.joint(f"    Max |dz_i|:       {torch.max(torch.abs(z_change)).item():.6e}\n")

        # Check if solution is within but near budget
        norm = torch.norm(z.detach(), 2)
        if norm > softmaxdata['budget']:
            # penalty param too small
            log.joint("  penalty parameter: {} too small, norm = {}\n".format(penalty_param, norm))
            pLeft = penalty_param
        elif norm < softmaxdata['budget'] - budget_threshold:
            # penalty param too big
            log.joint("  penalty parameter: {} too big, norm = {}\n".format(penalty_param, norm))
            if pRight - pLeft < interval_threshold:
                # search interval too small
                log.joint("  --> search interval too small, accept penalty parameter as is\n")
                done = True
            else:
                pRight = penalty_param
        else:
            # penalty param just right
            done = True

        breakexit("step")

    log.joint("  penalty parameter: {}\n".format(penalty_param))
    log.joint("    gradient converged? {}\n".format(gradientconverged))
    myshownparraythresh(log, z.detach().numpy(), len(z), "    zvalues", thresh=.0001,padding="     ")
    log.joint("    norm: {}\n".format(norm))
    log.joint("    logsumexp: {}\n".format(logsumexp_potential.item()))
    log.joint("    penalty: {}\n".format(penalty.item()))
    log.joint("    loss: {}\n".format(loss.item()))

    log.joint("STOP: PyTorch finished in %g secs, after %d rounds.\n"%(time.time()-start_time, n_rounds))

    # Remove coordinates smaller than threshold
    threshold = 1e-4
    z = torch.where(z < threshold, torch.tensor(0.0), z)
    log.joint("norm after clipping: %f\n"%(torch.norm(z.detach(), 2)))

    # Save zvalues of solution
    alldata['algo']['zvalues'][:] = z.detach().numpy()


    