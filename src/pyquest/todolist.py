import itertools
import random


class ToDoListGenerator():


# within means each user must do all
# between means that between them all users must do all

    # within-within
    def ww(self, tasks, interfaces):
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
    def wb(self, tasks, interfaces):
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
    def bw(self, tasks, interfaces):
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
    def bb(self, tasks, interfaces):
        permutations = []
        for task in tasks:
            for interface in interfaces:
                permutations.append([(task, interface)])
        return permutations

    def generate(self, toCall, tasks, interfaces, shuffle):
        toDoList = getattr(self, toCall)(tasks, interfaces)
        if shuffle:
            random.shuffle(toDoList)
        return toDoList

