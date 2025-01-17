#%%

#############
# Adam optimiser, train for u(x,t), then lambda_i
# lambda_i are not network parameters


# DiffEqLHS with true values of lambda 1 and 2 gives slightly larger loss
# increase learning rate and continue training on u(x,t)


# burgersSplit2.pth: network with only 4 layers
# burgersSplit3.pth: network with 8 layers, trained to 60000 epochs
# burgersSplit4.pth: network with from burgersSplit3.pth, 
#                   further trained after increasing lr to 1e-3
# burgersSplit5.pth: network with from burgersSplit3.pth,
#                   further trained after increasing lr to 1e-4 
#                   with scheduler patience = 5000
# burgersSplit6.pth: network with 8 layers, scheduler patience = 500
# burgersSplit7.pth: network with 8 layers, scheduler patience = 10000
#                      batchsize = numsamples
#############

import torch
import torch.utils.data
import torch.distributions
import numpy as np
import matplotlib.pyplot as plt
from torch.autograd import grad
import scipy.io


class DataSet(torch.utils.data.Dataset):
    """Creates range of evenly-spaced x- and y-coordinates as test data"""
    def __init__(self, XT, u_exact, numSamples):
        # generate numSamples random indices to get training sample
        idx = np.random.choice(XT.shape[0], numSamples, replace=False) 

        XT_train = torch.tensor(XT[idx,:], requires_grad=True).float()
        u_train = torch.tensor(u_exact[idx,:], requires_grad=True).float()

        # input of forward function must have shape (batch_size, 3)
        self.data_in = torch.cat((XT_train,u_train),1)
        
    def __len__(self):
        return self.data_in.shape[0]


    def __getitem__(self, i):
        return self.data_in[i,:]

class Fitter(torch.nn.Module):
    """Forward propagations"""

    def __init__(self, numHiddenNodes, numHiddenLayers):
        super(Fitter, self).__init__()
        # 3 inputs: x, t, u_exact values
        self.fc1 = torch.nn.Linear(3, numHiddenNodes)
        self.fcs = torch.nn.ModuleList([torch.nn.Linear(numHiddenNodes, numHiddenNodes)
                    for _ in range(numHiddenLayers-1)])
        # 1 output : u
        self.fcLast = torch.nn.Linear(numHiddenNodes, 1)

    def forward(self, input):
        hidden = torch.tanh(self.fc1(input))
        for i in range(len(self.fcs)):
            hidden = torch.tanh(self.fcs[i](hidden))
        # No activation function on final layer
        out = self.fcLast(hidden)
        return out

def trainU(network, lossFn, optimiser, scheduler, loader, numEpochs):
    """Trains the neural network to approximate u(x,t)"""
    costList=[]
    network.train(True)
    for _ in range(numEpochs):
        for batch in loader:
            # print(batch)
            u_out = network.forward(batch)
            # print(u_out)

            _, _, batch_u_exact = torch.split(batch,1, dim =1)
            # print(u_exact)

            loss = lossFn(u_out, batch_u_exact)

            loss.backward()
            optimiser.step()
            optimiser.zero_grad()

        # update scheduler, tracks loss and updates learning rate if on plateau   
        scheduler.step(loss)

        # store final loss of each epoch
        costList.append(loss.detach().numpy())

    print("current u train loss = ", loss.detach().numpy())     
    network.train(False)
    return costList

def trainDE(network, lambda1, lambda2, lossFn, optimiser, scheduler, loader, numEpochs):
    """Trains the neural network to approximate lambda1, lambda2"""
    costList=[]
    lambda1List = []
    lambda2List = []
    network.train(True)
    for _ in range(numEpochs):
        for batch in loader:
            # print(batch)
            u_out = network.forward(batch)
            # print(u_out)
            du = grad(u_out, batch, torch.ones_like(u_out), retain_graph=True, create_graph=True)[0]
            # print(du)
            d2u = grad(du, batch, torch.ones_like(du), retain_graph=True, create_graph=True)[0]
            # print(d2u)
            u_x, u_t, _ = torch.split(du, 1, dim =1)
            # print(u_t)
            # print(u_x)
            u_xx, u_tt, _ = torch.split(d2u, 1, dim =1)
            # print(u_xx)
            
            # With exponential for lambda2
            diffEqLHS = u_t + (lambda1 * u_out * u_x) - (torch.exp(lambda2) * u_xx)

            # Without exponential for lambda2
            # diffEqLHS = u_t + (lambda1 * u_out * u_x) - (lambda2 * u_xx)

            loss = lossFn(diffEqLHS, torch.zeros_like(diffEqLHS))

            loss.backward()

            # Examine grads on lambda1, lambda2
            # print("lambda1 grad = ", lambda1.grad.item())
            # print("lambda2 grad = ", lambda2.grad.item())
            optimiser.step()
            optimiser.zero_grad()

        # update scheduler, tracks loss and updates learning rate if on plateau   
        scheduler.step(loss)

        # store final loss of each epoch
        costList.append(loss.detach().numpy())
        lambda1List.append(lambda1.item())
        lambda2List.append(lambda2.item())

    print("current DE train loss = ", loss.detach().numpy())
    trueDiffEq = u_t + (u_out * u_x) - ((0.01/np.pi) * u_xx)
    trueLoss = lossFn(trueDiffEq, torch.zeros_like(trueDiffEq))
    print("DE with true lambda values = ", trueLoss.detach().numpy())

    
    print("lambda1 = ", lambda1.item())
    # With exponential for lambda2
    # print("lambda2 = ", torch.exp(lambda2))

    # Without exponential for lambda2
    print("lambda2 = ", lambda2.item())
    # print("lambda1 grad = ", lambda1.grad.item())
    # print("lambda2 grad = ", lambda2.grad.item())

    network.train(False)
    return costList, lambda1List, lambda2List

def test(network, lambda1, lambda2, XT, u_exact, lossFn):
    """
    Tests network solution on all 25600 sample points
    """
    testData = DataSet(XT , u_exact, XT.shape[0])
    batch = testData.data_in
    u_out = network.forward(batch)

    du = grad(u_out, batch, torch.ones_like(u_out), retain_graph=True, create_graph=True)[0]
    # print(du)

    d2u = grad(du, batch, torch.ones_like(du), retain_graph=True, create_graph=True)[0]
    # print(d2u) 

    u_x, u_t, _ = torch.split(du, 1, dim =1)
    # print(u_t)
    # print(u_x)

    u_xx, u_tt, _ = torch.split(d2u, 1, dim =1)
    # print(u_xx)

    # DE with exp(lambda2)
    diffEqLHS = u_t + (lambda1 * u_out * u_x) - (torch.exp(lambda2) * u_xx)

    # DE without exp(lambda2), i.e. just with lambda2
    # diffEqLHS = u_t + (lambda1 * u_out * u_x) - (lambda2 * u_xx)

    # calculate losses for u, DE, lambda1 and lambda2
    uTestLoss = lossFn(u_out, batch[:,2].view(-1,1))
    DETestLoss = lossFn(diffEqLHS, torch.zeros_like(diffEqLHS))
    lambda1Loss = abs(lambda1 - 1.) * 100
    lambda2Loss = (abs(torch.exp(lambda2) - ( 0.01 / np.pi)) / (0.01 / np.pi)) * 100
    # lambda2Loss = (abs(lambda2 - ( 0.01 / np.pi)) / (0.01 / np.pi)) * 100
    print("u_test error = ", uTestLoss.item())
    print("DE_test error = ", DETestLoss.item())
    print("lambda1 error = ", lambda1Loss.item(), " %")
    print("lambda2 error = ", lambda2Loss.item(), " %")
    return


def plotNetwork(network, X, T, XT, u_exact, epoch):
    """
    Plots network solution for all 25600 sample points
    """
    XT = torch.tensor(XT).float().to(device)
    u_exact = torch.tensor(u_exact).float().to(device)

    input = torch.cat((XT,u_exact),1)
    # print(X)
    # print(T)
    u_out = network.forward(input)
    # print(u_out)
    u_out = u_out.reshape(X.shape[0],X.shape[1])
    # print(u_out)
    u_out = u_out.detach().numpy()

    # print("lambda1 = ", lambda1.item())
    # print("lambda2 = ", torch.exp(lambda2).item())
    # print("lambda2 = ", lambda2.item())


    # print(X.shape)
    # print(T.shape)
    # print(u_out.shape)

    # Plot trial solution
    ax = plt.axes(projection='3d')
    ax.plot_surface(X,T,u_out,rstride=1, cstride=1,
                cmap='plasma', edgecolor='none')
    ax.set_xlabel('x')
    ax.set_ylabel('t')
    
    # Plot exact solution
    # ax.scatter(X,T,u_exact, label = 'Exact Solution')
    # ax.legend()

    ax.set_title(str(epoch) + " Epochs")
    plt.show()
    return

# load and format sample data (dictionary) for u(x,t)
# there are 25600 samples in total 
data = scipy.io.loadmat('burgersData.mat')

t = data['t'].flatten()[:,None]
x = data['x'].flatten()[:,None]
Exact = np.real(data['usol']).T
# print(Exact)

X, T = np.meshgrid(x,t)

XT = np.hstack((X.flatten()[:,None], T.flatten()[:,None]))
# `print(XT.shape)
u_exact = Exact.flatten()[:,None]
# print(u_exact)
# print(u_exact.reshape(X.shape[0],X.shape[1]))
# print(u_exact.shape)

# number of training samples
numSamples = 2000

if torch.cuda.is_available():
    print("cuda time")
    device=torch.device("cuda")
else:
    print("sorry no cuda for yuda")
    device=torch.device("cpu")

try: # load saved network if possible
    checkpoint = torch.load('burgersSplitGPU.pth')
    epoch = checkpoint['epoch']
    network = checkpoint['network']
    optimiser = checkpoint['optimiser']
    scheduler = checkpoint['scheduler']
    uLosses = checkpoint['uLosses']
    trainData = checkpoint['trainData']
    print("model loaded")
except: # create new network
    epoch = 0
    network    = Fitter(numHiddenNodes=32, numHiddenLayers=8).to(device)
    optimiser  = torch.optim.Adam(network.parameters(), lr = 1e-3)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimiser, 
        factor=0.5, 
        patience=10000, 
        threshold=1e-4, 
        cooldown=0, 
        min_lr=1e-6, 
        eps=1e-8, 
        verbose=True
    )
    trainData = DataSet(XT, u_exact, numSamples)
    uLosses = []
    print("model created")

trainLoader = torch.utils.data.DataLoader(dataset=trainData, batch_size=int(numSamples), shuffle=True)
lossFn   = torch.nn.MSELoss()
# for n in network.parameters():
#     print(n)

numEpochs = 1000 # number of epochs to train each iteration
totalEpochs = 800000
while epoch < totalEpochs:
    newLoss = trainU(network, lossFn, optimiser, scheduler, trainLoader, numEpochs)
    uLosses.extend(newLoss)
    epoch += numEpochs

    if epoch != 0:
        if epoch % 10000 == 0:
            plotNetwork(network, X, T, XT, u_exact, epoch)

            plt.semilogy(uLosses)
            plt.xlabel("Epochs")
            plt.ylabel("Loss")
            plt.title("Loss")
            plt.show()
        if epoch % 20000 == 0:
            # save network
            checkpoint = { 
                'epoch': epoch,
                'network': network,
                'optimiser': optimiser,
                'scheduler': scheduler,
                'uLosses': uLosses,
                'trainData': trainData
                }
            torch.save(checkpoint, 'burgersSplit7.pth')
            print("model saved")


lambda1 = torch.tensor(torch.rand(1), requires_grad = True).to(device) 
lambda2 = torch.tensor(torch.rand(1), requires_grad = True).to(device)

# lambda1 = torch.tensor(0., requires_grad = True) 
# lambda2 = torch.tensor(0.002479, requires_grad = True)  

plotNetwork(network, X, T, XT, u_exact, epoch)
test(network, lambda1, lambda2, XT, u_exact, lossFn)

optimiser  = torch.optim.Adam([{"params": lambda1, 'lr' : 1e-3},
                                {"params": lambda2, 'lr' : 1e-3}], lr = 1e-3)

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimiser, 
    factor=0.5, 
    patience=1000, 
    threshold=1e-4, 
    cooldown=0, 
    min_lr=0, 
    eps=1e-8, 
    verbose=True
)

DELosses = []
lambda1List = []
lambda2List = []
iterations = 0
numEpochs = 1000 # number of epochs to train each iteration
while iterations < 30:
    newLoss, newLambda1, newLambda2 = trainDE(network, lambda1, lambda2, lossFn, optimiser, scheduler, trainLoader, numEpochs)
    DELosses.extend(newLoss)
    lambda1List.extend(newLambda1)
    lambda2List.extend(newLambda2)
    iterations += 1

    plotNetwork(network, X, T, XT, u_exact, epoch)

    plt.plot(lambda1List)
    plt.xlabel("Epochs")
    plt.ylabel("Lambda 1")
    plt.title("Lambda 1")
    plt.show()

    plt.plot(lambda2List)
    plt.xlabel("Epochs")
    plt.ylabel("Lambda 2")
    plt.title("Lambda 2")
    plt.show()

    plt.semilogy(DELosses)
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.title("Differential Equation Loss")
    plt.show()

print("Final value of lambda1 = ", lambda1.item())
print("Final value of lambda2 = ", torch.exp(lambda2).item())
# print("Final value of lambda2 = ", lambda2.item())
print("True value of lambda1 = ", 1.0)
print("True value of lambda2 = ", 0.01 / np.pi)
test(network, lambda1, lambda2, XT, u_exact, lossFn)
# for n in network.parameters():
#     print(n)

# %%
