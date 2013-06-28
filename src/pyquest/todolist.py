import itertools
import random

# within means each user must do all
# between means that between them all users must do all

# within-within
def ww(tasks, interfaces):
    permutations = []
    for task in tasks:
        for interface in interfaces:
            permutations.append((task, interface))
            firstPermute = itertools.permutations(permutations)
    
# itertools.permutations will return a tuple of tuples of tuples
# but we want a list of lists of tuples so reconstruct
    permutations = []
    for perm in firstPermute:
           permutations.append(list(perm))
    return permutations

# within-between
def wb(tasks, interfaces):
    permutations = []
    taskperms = itertools.permutations(tasks)
    for taskperm in taskperms:
        for interface in interfaces:
            perm = []
            for i in range(len(taskperm)):
                perm.append((taskperm[i], interface))
                permutations.append(perm)
    return permutations

# between-within
def bw(tasks, interfaces):
    permutations = []
    intperms = itertools.permutations(interfaces)
    for intperm in intperms:
        for task in tasks:
            perm = []
            for i in range(len(intperm)):
                perm.append((task, intperm[i]))
            permutations.append(perm)
    return permutations

# between-between
def bb(tasks, interfaces):
    permutations = []
    for task in tasks:
        for interface in interfaces:
            permutations.append([(task, interface)])
    return permutations

def constructLists(task_count, interface_count):
    tasks = []
    for i in range(2):
        tasks.append(chr(i+65))
    interfaces = range(1, 3)
    return (tasks, interfaces)

def generate(toCall, task_count, interface_count, shuffle):
    tandi = constructLists(task_count, interface_count)
    toDoList = globals()[toCall](tandi[0], tandi[1])
    if shuffle:
        random.shuffle(toDoList)
    return toDoList

