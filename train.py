import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from CapsNet import capsules

def one_hot_embedding(labels, num_classes):
    shape =list(labels.shape)
    shape.append(num_classes)
    if labels.is_cuda:
        y = torch.zeros(shape).cuda()
    else:
        y = torch.zeros(shape)
    
    for index in range(list(y.shape)[0]):
        y[index][labels[index]]= 1

    return y

def train(args, model, device, train_loader, optimizer, epoch,use_cuda):
    model.train()
    correct = 0

    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        target = one_hot_embedding(target,num_classes=10  )
        criterion =nn.MSELoss()
        loss= criterion(output, target)
        loss.backward()
        optimizer.step()
        
        
        if batch_idx % args.log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                100. * batch_idx / len(train_loader), loss.item()))


def test(args, model, device, test_loader,use_cuda):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            target = one_hot_embedding(target,num_classes=10  )
            test_loss += F.mse_loss(output, target)

    test_loss /= len(test_loader.dataset)

    print('Test Loss: {:.6f}'.format( test_loss.item()))


def main():
    # Training settings
    parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
    parser.add_argument('--batch-size', type=int, default=10, metavar='N',
                        help='input batch size for training (default: 64)')
    parser.add_argument('--test-batch-size', type=int, default=10, metavar='N',
                        help='input batch size for testing (default: 1000)')
    parser.add_argument('--epochs', type=int, default=10, metavar='N',
                        help='number of epochs to train (default: 10)')
    parser.add_argument('--lr', type=float, default=0.01, metavar='LR',
                        help='learning rate (default: 0.01)')
    parser.add_argument('--momentum', type=float, default=0.5, metavar='M',
                        help='SGD momentum (default: 0.5)')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA training')
    parser.add_argument('--seed', type=int, default=1337, metavar='S',
                        help='random seed (default: 1)')
    parser.add_argument('--log-interval', type=int, default=10, metavar='N',
                        help='how many batches to wait before logging training status')

    args = parser.parse_args()
    use_cuda = not args.no_cuda and torch.cuda.is_available()

    torch.manual_seed(args.seed)

    device = torch.device("cuda" if use_cuda else "cpu")

    kwargs = {'num_workers': 1} if use_cuda else {}
    train_loader = torch.utils.data.DataLoader(
        datasets.MNIST('./data/mnist', train=True, download=True,
                       transform=transforms.Compose([
                           transforms.ToTensor(),
                           transforms.Normalize((0.1307,), (0.3081,))
                       ])),
        batch_size=args.batch_size, shuffle=True, **kwargs)
    test_loader = torch.utils.data.DataLoader(
        datasets.MNIST('./data/mnist', train=False, transform=transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,))
        ])),
        batch_size=args.test_batch_size, shuffle=True, **kwargs)

    A, B, C, D = 64, 8, 16, 16
    model = capsules(A=A, B=B, C=C, D=D, E=10,
                     iters=2, cuda=use_cuda).to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr,)

    for epoch in range(1, args.epochs + 1):
        train(args, model, device, train_loader, optimizer, epoch,use_cuda)
        test(args, model, device, test_loader,use_cuda)

    torch.save(model.state_dict(), "./mnist_capsules.pth")


if __name__ == '__main__':
    main()
