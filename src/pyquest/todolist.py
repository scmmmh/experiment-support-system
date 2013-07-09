import itertools
import random

# within means each user must do all
# between means that between them all users must do all

# within-within
def ww(tasks, interfaces):
    combinations = []
    for task in tasks:
        for interface in interfaces:
            combinations.append((task, interface))
    print "Combinations %s" % str(combinations)
    permutations = [list(i) for i in itertools.permutations(combinations)]
    
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

def constructTaskLists(task_count, task_disallow):
    tasks = [] 
    for i in range(task_count):
        tasks.append(chr(i+65))

    taskLists = []
    if task_disallow and len(task_disallow) > 0:
        for group in task_disallow:
            print "\nDISALLOWING %s\n" % str(group)
            for d in group:
                tasksClone = list(tasks)
                for e in group:
                    if e != d:
                        tasksClone.remove(e)
                print "APPENDING %s\n" % str(tasksClone)
                taskLists.append(tasksClone)
    else:
        taskLists.append(tasks)
    return taskLists

def constructInterfaceLists(interface_count, interface_disallow):
    interfaces = range(1, interface_count + 1)
    return [interfaces]

def generate(toCall, task_count, interface_count, shuffle, task_disallow):
    taskLists = constructTaskLists(task_count, task_disallow)
    interfaceLists = constructInterfaceLists(interface_count, None)

    toDoList = []
    for i in range(len(taskLists)):
        for j in range(len(interfaceLists)):
            toDoList = toDoList + globals()[toCall](taskLists[i], interfaceLists[j])

    if shuffle:
        random.shuffle(toDoList)

    return toDoList

