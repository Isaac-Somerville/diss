#%%

import torch
# from torch.autograd import grad
# import torch.nn as nn
# import torch.optim as optim
import numpy as np
import scipy.io
import matplotlib.pyplot as plt

# data = scipy.io.loadmat('burgersData.mat')

# t = torch.tensor(data['t'].flatten()[:,None])
# x = torch.tensor(data['x'].flatten()[:,None])
# Exact = np.real(data['usol']).T

# X, T = np.meshgrid(x,t)
# print(X.shape)
# print(T.shape)

# X_star = np.hstack((X.flatten()[:,None], T.flatten()[:,None]))
# u_star = Exact.flatten()[:,None]   
# print(t)
# print(x)
# print(Exact.shape)
# print(X)
# print(T)
# print(X_star.shape)
# print(u_star.shape)

# idx = np.random.choice(X_star.shape[0], 2000, replace=False)
# X_u_train = X_star[idx,:]
# u_train = u_star[idx,:]
# print(idx)
# print(X_u_train.shape)
# print(u_train.shape)
# # x = [[1,2,3],
# #      [4,5,6],
# #      [7,8,9]]

# # print([x[i][0] for i in range(3)])

# # amount = 4
# # dp = [amount +1] * (amount + 1)
# # print(dp)

# # x = torch.tensor([[1,2],
# #                   [3,4],
# #                   [5,6]])

# # x = x.detach().numpy()
# # print(x)

# # y = torch.tensor([[-1,1],
# #                   [3,5],
# #                   [7,9]])

# # y = y.detach().numpy()
# # print(y)

# # print(np.square(x-y).mean())


# # x = [[1,2,3],
# #      [4,5,6]]

# # y = np.array(x)
# # print(y.shape)
# # z = np.exp(y)
# # print(z)

# # coordinates = (0,0,2)
# # print(y[coordinates])

# # x = [0,1,2]
# # y = torch.tensor(x)
# # print(y.size(dim = 0))

# # def exp_reducer(x):
# #   return x.exp().sum(dim=0)
# # inputs = torch.rand(2, 5)
# # print(inputs)
# # print(inputs.exp())
# # print(exp_reducer(inputs))
# # print(jacobian(exp_reducer, inputs))

# # print(jacobian(exp_reducer, inputs).shape)

# # def exp_adder(x, y):
# #      # print(2* x.exp())
# #      # print(3 * y)

# #      return 2 * x.exp() + 3 * y
# # inputs = (torch.rand(2), torch.rand(2))
# # print(inputs)
# # print(exp_adder(inputs[0],inputs[1]))
# # jacobian(exp_adder, inputs)

# class net_x(nn.Module): 
#         def __init__(self):
#             super(net_x, self).__init__()
#             self.fc1=nn.Linear(2, 20) 
#             self.fc2=nn.Linear(20, 20)
#             self.out=nn.Linear(20, 4) #a,b,c,d

#         def forward(self, x):
#             x=torch.tanh(self.fc1(x))
#             x=torch.tanh(self.fc2(x))
#             x=self.out(x)
#             return x

# nx = net_x()

# #input

# val = 10
# a = torch.rand(val, requires_grad = True) #input vector
# print(a)
# t = torch.reshape(a, (5,2)) #reshape for batch
# print(t)

# # #method 
# # dx = torch.autograd.functional.jacobian(nx, t)
# # print(dx.shape)
# # print(dx)
# # print(torch.diagonal(dx,0,-1))
# # #dx = torch.diagonal(torch.diagonal(dx, 0, -1), 0)[0] #first vector
# # dx = torch.diagonal(torch.diagonal(dx, 1, -1), 0)[0] #2nd vector
# # #dx = torch.diagonal(torch.diagonal(dx, 2, -1), 0)[0] #3rd vector
# # #dx = torch.diagonal(torch.diagonal(dx, 3, -1), 0)[0] #4th vector
# # print(dx)

# print(a.grad)
# out = nx(t)
# m = torch.zeros((5,4))
# print(m)
# m[:, 0] = 1
# print(m)
# out.backward(m)
# print(a.grad)

# ######### Loss surface examples
# xrange = [-0.2,1.9]
# yrange = [0.7,2.9]

# # xrange = [-5,5]
# # yrange = [-5,5]
# num_samples = 50
# x_lin  = torch.linspace(xrange[0],xrange[1],num_samples)
# y_lin  = torch.linspace(yrange[0],yrange[1],num_samples)
# X,Y = torch.meshgrid(x_lin,y_lin)
# x, y  = X.reshape(-1,1), Y.reshape(-1,1)

# def solution(x, y):
#     return -0.1 * (torch.cos(np.pi * 2*x) + torch.cos(np.pi *2* y) -x**2 - y **2) +0.2


# # Plot trial and exact solutions
# ax = plt.axes(projection='3d')
# surface = solution(X,Y)
# X = X.detach().numpy()
# Y = Y.detach().numpy()
# ax.plot_surface(X,Y,surface,rstride=1, cstride=1,
#             cmap='viridis', edgecolor='none')
# ax.view_init(35, 210)
# ax.set_ylabel('b',fontsize = 16)
# ax.set_xlabel('w', fontsize = 16)
# ax.set_title('Error Surface J(w,b)', fontsize = 16)
# plt.show()

# #########

xrange = [-30,30]
xLin = np.linspace(xrange[0], xrange[1], 100)
plt.axhline(y=0, color='0.8')
plt.axvline(x=0, color='0.8')
plt.xlabel('x', fontsize = 16)
plt.ylabel('y', fontsize = 16)


def sigmoid(x):
    return  1 / (1+np.exp(-x))

def dsigmoid(x):
    return sigmoid(x) * (1-sigmoid(x))

# sig = [sigmoid(x) for x in xLin]
# dsig = [dsigmoid(x) for x in xLin]
# plt.plot(xLin, sig, label = '\u03C3(x)')
# plt.plot(xLin, dsig, label = "\u03C3'(x)")
# plt.ylabel('y', fontsize = 16)
# plt.title("\u03C3(x) and \u03C3'(x)", fontsize = 16)

# plt.title("tanh(x) and tanh'(x)", fontsize = 16)
# tanh = [np.tanh(x) for x in xLin]
# dtanh = [(1-np.tanh(x)**2) for x in xLin]
# plt.plot(xLin,tanh, label = "tanh(x)")
# plt.plot(xLin,dtanh, label = "tanh'(x)")

# def reLU(x):
#     return max(0,x)

# def dreLU(x):
#     return 0 if x <= 0 else 1

# # plt.ylabel('ReLU(x)', fontsize = 16)
# xLin1 = np.linspace(-6, 0, 50)
# xLin2 = np.linspace(1e-8, 6, 50)
# plt.title("ReLU(x) and ReLU'(x)", fontsize = 16)
# relu = [reLU(x) for x in xLin]
# drelu = [dreLU(x) for x in xLin1]
# plt.plot(xLin,relu,label = "ReLU(x)")
# plt.plot(xLin1,drelu,label = "ReLU'(x)")
# drelu = [dreLU(x) for x in xLin2]
# plt.plot(xLin2,drelu,color = 'orange')

# def LeakyReLU(x):
#     return max(0.01*x,x)

def swish(x, beta):
    return x * sigmoid(beta*x)

def dswish(x,beta):
    return sigmoid(beta*x) + x * beta * dsigmoid(beta*x)

betas = [0.1, 1, 10]
for beta in betas:
    swis = [swish(x,beta) for x in xLin]
    plt.plot(xLin, swis, label = '\u03BC = ' + str(beta))
    plt.title("Swish(x) = x\u03C3(\u03BCx)", fontsize = 16)
    plt.legend(loc = "upper left", fontsize = 16)
plt.show()

for beta in betas:
    dswis = [dswish(x,beta) for x in xLin]
    plt.axhline(y=0, color='0.8')
    plt.axvline(x=0, color='0.8')
    plt.xlabel('x', fontsize = 16)
    plt.ylabel('y', fontsize = 16)  
    plt.plot(xLin, dswis, label = '\u03BC = ' + str(beta))
    plt.title("Swish'(x) = \u03C3(\u03BCx) + \u03BCx\u03C3(\u03BCx)(1 - \u03C3(\u03BCx))", fontsize = 16)
    plt.legend(loc = "upper left", fontsize = 16)
plt.show()



# plt.ylabel('Leaky ReLU(x)', fontsize = 16)
# plt.title('Leaky ReLU', fontsize = 16)
# relu = [LeakyReLU(x) for x in xLin]
# plt.plot(xLin,relu)

# plt.ylabel('Linear(x)', fontsize = 16)
# plt.title("Linear(x) and Linear'(x)", fontsize = 16)
# dxLin = [1 for _ in range(len(xLin))]
# plt.plot(xLin,xLin,label = "Linear(x)")
# plt.plot(xLin,dxLin,label = "Linear'(x)")




print(int(2250000/2250000 * 3))




# %%
