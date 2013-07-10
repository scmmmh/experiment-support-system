import itertools
import math
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
    for interface in interfaces:
        combinations = []
        for task in tasks:
            combinations.append((task, interface))
        print "Combinations %s" % str(combinations)
        permutations = permutations + [list(i) for i in itertools.permutations(combinations)]
    return permutations;

# between-within
def bw(tasks, interfaces):
    permutations = []
    for task in tasks:
        combinations = []
        for interface in interfaces:
            combinations.append((task, interface))
        print "Combinations %s" % str(combinations)
        permutations = permutations + [list(i) for i in itertools.permutations(combinations)]
    return permutations;

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
        ctk = list(itertools.product(*task_disallow))
#        print "combinations to keep %s " % str(ctk)
        ctr = []
        for i in range(len(ctk)):
            tk = ctk[i]
            td = task_disallow
#            print "tk %s td %s" % (tk, td)
            tr = ()
            for j in range(len(tk)):
                tr = tr + tuple(td[j].replace(tk[j], ''))
#            print "tr %s td %s" % (tr, td)
            ctr.append(tr)
#        print "combinations to remove %s " % str(ctr)
        for group in ctr:
#            print "REMOVING %s" % str(group)
            tasksClone = list(tasks)
            for d in group:
                tasksClone.remove(d)
#            print "APPENDING %s\n" % str(tasksClone)
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

def calculate(toCall, task_count, interface_count, shuffle, task_disallow):
    taskLists = constructTaskLists(task_count, task_disallow)
    interfaceLists = constructInterfaceLists(interface_count, None)

    count = 0;
    for taskList in taskLists:
        for interfaceList in interfaceLists:
            print "taskList %s interfaceList %s" % (str(taskList), str(interfaceList))
            print "adding %d!" % (len(taskList) * len(interfaceList))
            count = count + math.factorial(len(taskList) * len(interfaceList))

    return count
