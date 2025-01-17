#%%
import torch
import torch.utils.data
import numpy as np
import matplotlib.pyplot as plt
from torch.autograd import grad
import time

class DataSet(torch.utils.data.Dataset):
    """
    An object which generates the x values for the input node 
    """
    def __init__(self, numSamples, xRange):
        """
        Arguments:
        xRange (list of length 2) -- lower and upper limits for input values x
        numSamples (int) -- number of training data samples

        Returns:
        DataSet object with one attributes:
            dataIn (PyTorch tensor of shape (numSamples,1)) -- 'numSamples'
                evenly-spaced data points from xRange[0] to xRange[1]
        """
        self.dataIn  = torch.linspace(xRange[0], xRange[1], numSamples, requires_grad=True).view(-1,1)
        # 'view' method reshapes tensors, in this case into a column vector

    def __len__(self):
        """
        Arguments:
        None

        Returns:
        len(self.dataIn) (int) -- number of training data points
        """
        return len(self.dataIn)

    def __getitem__(self, idx):
        """
        Used by DataLoader object to retrieve training data points

        Arguments:
        idx (int) -- index of data point required
        
        Returns:
        x (tensor shape (1,1)) -- data point at index 'idx'
        """
        return self.dataIn[idx]
    
class Fitter(torch.nn.Module):
    """
    The neural network object, with 1 node in the input layer,
    1 node in the output layer, and 1 hidden layer with 'numHiddenNodes' nodes.
    """
    def __init__(self, numHiddenNodes):
        """
        Arguments:
        numHiddenNodes (int) -- number of nodes in hidden layer

        Returns:
        Fitter object (neural network) with two attributes:
        fc1 (fully connected layer) -- linear transformation of hidden layer
        fc2 (fully connected layer) -- linear transformation of outer layer
        """
        super(Fitter, self).__init__()
        self.fc1 = torch.nn.Linear(in_features = 1, out_features = numHiddenNodes)
        self.fc2 = torch.nn.Linear(in_features = numHiddenNodes, out_features = 1)

    def forward(self, x):
        """
        Function which connects inputs to outputs in the neural network.

        Arguments:
        x (PyTorch tensor shape (batchSize,1)) -- input of neural network

        Returns:
        y (PyTorch tensor shape (batchSize,1)) -- output of neural network
        """
        # tanh activation function used on hidden layer
        h = torch.tanh(self.fc1(x))
        # Linear activation function used on outer layer
        y = self.fc2(h)
        return y

def train(network, loader, lossFn, optimiser, numEpochs):
    """
    A function to train a neural network to solve a 
    second-order ODE with Cauchy boundary conditions.

    Arguments:
    network (Module) -- the neural network
    loader (DataLoader) -- generates batches from the training dataset
    lossFn (Loss Function) -- network's loss function
    optimiser (Optimiser) -- carries out parameter optimisation
    numEpochs (int) -- number of training epochs

    Returns:
    cost_list (list of length 'numEpochs') -- cost values of all epochs
    """
    cost_list=[]
    network.train(True)
    for epoch in range(numEpochs):
        for batch in loader:
            n_out = network(batch)

            # Get first derivative of the network output with respect to the input values: 
            dndx = grad(n_out, batch, torch.ones_like(n_out), retain_graph=True, create_graph=True)[0]
            # Get second derivative of the network output with respect to the input values: 
            d2ndx2 =grad(dndx, batch, torch.ones_like(dndx), retain_graph=True)[0]
            
            # Get value of trial solution f(x)
            f_trial = trialFunc(batch, n_out)
            # Get f'(x)
            df_trial = dTrialFunc(batch, n_out, dndx)
            # Get f''(x)
            d2f_trial = d2TrialFunc(batch,n_out,dndx,d2ndx2)
            # Get LHS of differential equation D(x) = 0
            diff_eq = diffEq(batch, f_trial, df_trial, d2f_trial)
            
            cost = lossFn(diff_eq, torch.zeros_like(diff_eq)) # calculate cost
            # torch.zeros_like(x) creates a tensor the same shape as x, filled with 0's
            cost.backward() # perform backpropagation
            optimiser.step() # perform parameter optimisation
            optimiser.zero_grad() # reset gradients to zero

        cost_list.append(cost.detach().numpy())# store cost of each epoch
    network.train(False)
    return cost_list


def plotNetwork(network, epoch):
    x    = torch.linspace(-5, 15, 120, requires_grad=True).view(-1,1)
    N    = network.forward(x)
    f_trial = trialFunc(x, N)
    dndx = grad(N, x, torch.ones_like(N), retain_graph=True, create_graph=True)[0]  
    d2ndx2 =grad(dndx, x, torch.ones_like(dndx), retain_graph=True)[0]
    df_trial = dTrialFunc(x, N, dndx)
    d2f_trial = d2TrialFunc(x,N,dndx,d2ndx2)
    diff_eq = diffEq(x, f_trial, df_trial, d2f_trial)
    cost = lossFn(diff_eq, torch.zeros_like(diff_eq))
    print("test cost = ", cost.item())

    # x1    = torch.linspace(-5, 0, 20, requires_grad=True).view(-1,1)
    # N1    = network.forward(x1)
    # f_trial1 = trialFunc(x1, N1)
    # dndx = grad(N1, x1, torch.ones_like(N1), retain_graph=True, create_graph=True)[0]  
    # d2ndx2 =grad(dndx, x1, torch.ones_like(dndx), retain_graph=True)[0]
    # df_trial = dTrialFunc(x1, N1, dndx)
    # d2f_trial = d2TrialFunc(x1,N1,dndx,d2ndx2)
    # diff_eq = diffEq(x1, f_trial1, df_trial, d2f_trial)
    # cost = lossFn(diff_eq, torch.zeros_like(diff_eq))
    # print("test cost = ", cost.item())

    # x2    = torch.linspace(10, 15, 20, requires_grad=True).view(-1,1)
    # N2    = network.forward(x2)
    # f_trial2 = trialFunc(x2, N2)
    # dndx = grad(N2, x2, torch.ones_like(N2), retain_graph=True, create_graph=True)[0]  
    # d2ndx2 =grad(dndx, x2, torch.ones_like(dndx), retain_graph=True)[0]
    # df_trial = dTrialFunc(x2, N2, dndx)
    # d2f_trial = d2TrialFunc(x2,N2,dndx,d2ndx2)
    # diff_eq = diffEq(x2, f_trial2, df_trial, d2f_trial)
    # cost = lossFn(diff_eq, torch.zeros_like(diff_eq))
    # print("test cost = ", cost.item())

    exact = solution(x)
    MSECost = lossFn(f_trial, exact)
    print("MSE between trial and exact solution = ", MSECost.item())
    exact = exact.detach().numpy()
    x = x.detach().numpy()
    N = N.detach().numpy()
    plt.plot(x, trialFunc(x,N), 'r-', label = "Neural Network Output")
    plt.plot(x, exact, 'b.', label = "True Solution")
    # plt.plot(x, exact, 'b.', label = "True Solution, Training Range")


    # exact1 = solution(x1)
    # MSECost = lossFn(f_trial1, exact1)
    # print("MSE between trial and exact1 solution = ", MSECost.item())
    # exact1 = exact1.detach().numpy()
    # x1 = x1.detach().numpy()
    # N1 = N1.detach().numpy()
    # plt.plot(x1, trialFunc(x1,N1), 'r-')
    # plt.plot(x1, exact1, 'g.', label = "True Solution, New Range")

    # exact2 = solution(x2)
    # MSECost = lossFn(f_trial2, exact2)
    # print("MSE between trial and exact2 solution = ", MSECost.item())
    # exact2 = exact2.detach().numpy()
    # x2 = x2.detach().numpy()
    # N2 = N2.detach().numpy()
    # plt.plot(x2, trialFunc(x2,N2), 'r-')
    # plt.plot(x2, exact2, 'g.')
    
    plt.xlabel("x", fontsize = 16)
    plt.ylabel("f(x)", fontsize = 16)
    plt.legend(loc = "upper right", fontsize = 16)
    plt.title("Lagaris Problem 3: " + str(epoch) + " Epochs", fontsize = 16)
    # plt.title("Lagaris Problem 3: Right Extrapolation", fontsize = 16)
    # ax = plt.gca()
    # ax.set_ylim([-4, 2.7])
    # ax.set_xlim([100, 20100])
    plt.show()
    return
    

def trialFunc(x, n_out):
    """
    Trial solution to Lagaris problem 3: f(x) = x + x^2 * N(x)
    Arguments:
        x (tensor of shape (batchSize,1)) -- input of neural network
        n_out (tensor of shape (batchSize,1)) -- output of neural network
    Returns:
        x + (x**2 * n_out) (tensor of shape (batchSize,1)) -- trial solution to differential equation""" 
    return x + (x**2 * n_out)

def dTrialFunc(x, n_out, dndx):
    """
    First derivative of trial solution to Lagaris problem 3: f'(x) = 1 + 2xN(x) + x^2 * N'(x)
    Arguments:
        x (tensor of shape (batchSize,1)) -- input of neural network
        n_out (tensor of shape (batchSize,1)) -- output of neural network
        dndx (tensor of shape (batchSize,1)) -- derivative of n_out w.r.t. x
    Returns:
        1 + (2*x*n_out) + (x**2 * dndx) (tensor of shape (batchSize,1)) -- 1st derivative of trial function w.r.t. x)""" 
    return 1 + (2*x*n_out) + (x**2 * dndx)

def d2TrialFunc(x,n_out,dndx,d2ndx2):
    """
    Second derivative of trial solution to Lagaris problem 3: f''(x) = 2N(x) + (4x * N'(x)) + x^2 N''(x)
    Arguments:
        x (tensor of shape (batchSize,1)) -- input of neural network
        n_out (tensor of shape (batchSize,1)) -- output of neural network
        dndx (tensor of shape (batchSize,1)) -- 1st derivative of n_out w.r.t. x
        d2ndx2 (tensor of shape (batchSize,1)) -- 2nd derivative of n_out w.r.t. x
    Returns:
        2*n_out + (4*x*dndx) + (x**2 * d2ndx2) (tensor of shape (batchSize,1)) -- 2nd derivative of trial function w.r.t. x)""" 
    return 2*n_out + (4*x*dndx) + (x**2 * d2ndx2)

def diffEq(x, f_trial, df_trial, d2f_trial):
    """
    Returns D(x) of differential equation D(x) = 0 from Lagaris problem 3
    Arguments:
        x (tensor of shape (batchSize,1)) -- input of neural network
        f_trial (tensor of shape (batchSize,1)) -- trial solution at x
        df_trial (tensor of shape (batchSize,1)) -- 1st derivative of trial solution at x
        d2f_trial (tensor of shape (batchSize,1)) -- 2nd derivative of trial solution at x
    Returns:
        LHS - RHS (tensor of shape (batchSize,1)) -- differential equation evaluated at x"""
    LHS = d2f_trial + (1/5)*df_trial + f_trial
    RHS = -(1/5) * torch.exp(-x/5) * torch.cos(x)
    return LHS - RHS

def solution(x):
    """
    Analytic solution to Lagaris problem 3
    Arguments:
        x (tensor of shape (batchSize,1)) -- input of neural network
    Returns:
        torch.exp(-x/5) * torch.sin(x) (tensor of shape (batchSize,1)) -- analytic solution of differential equation at x"""
    return torch.exp(-x/5) * torch.sin(x)
    

try: # load saved network and cost list, if possible
    checkpoint = torch.load('problem3InitialNetwork.pth')
    network    = checkpoint['network']
    costList   = checkpoint['costList']
except: # create new network and cost list
    network     = Fitter(numHiddenNodes=10)
    costList    = []
    checkpoint  = {'network': network,
                  'costList': costList}
    torch.save(checkpoint, 'problem3InitialNetwork.pth')

# networkName  = 'Network1'
networkName  = 'Network2'

xRange       = [0, 10]
numSamples   = 50
batchSize    = 50
trainData    = DataSet(numSamples, xRange)
trainLoader  = torch.utils.data.DataLoader(dataset=trainData, batch_size=batchSize, shuffle=True)

xRangeWide       = [-5, 15]
numSamplesWide   = 100
batchSizeWide    = 100
trainDataWide    = DataSet(numSamplesWide, xRangeWide)
trainLoaderWide  = torch.utils.data.DataLoader(dataset=trainDataWide, batch_size=batchSizeWide, shuffle=True)

lossFn      = torch.nn.MSELoss()
optimiser   = torch.optim.Adam(network.parameters(), lr=1e-3)
epoch       = 0 
numEpochs   = 1000
totalEpochs = 40000

start = time.time()
while epoch < totalEpochs:
    if networkName == 'Network1' and epoch < 20000:
        costList.extend(train(network, trainLoader, lossFn, optimiser, numEpochs))
    else:
        costList.extend(train(network, trainLoaderWide, lossFn, optimiser, numEpochs))
    epoch += numEpochs
end = time.time()

checkpoint  = {'network': network,
                'costList': costList,}
torch.save(checkpoint, 'problem3' + networkName + '.pth')

print("total time elapsed = ", end-start, " seconds")
print(epoch, "epochs total, final cost = ", costList[-1])

plotNetwork(network, epoch)
plt.semilogy(costList)
plt.xlabel("Epochs",fontsize = 16)
plt.ylabel("Cost",fontsize = 16)
plt.title("Lagaris Problem 3: Training Cost",fontsize = 16)
plt.show()
