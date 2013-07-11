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


def constructLists(factors, disallow):
    """ Constructs the sublists of combinations needed according to the restrictions passed in. So, for example, if passed 
    ['A', 'B', 'C', 'D', 'E'] as factors and ['AB'] as disallow it will return the two lists ['A', 'C', 'D', 'E']
    and ['B', 'C', 'D', 'E']. It is done as 'to keep' and then 'to remove' in order to handle cases where disallowed 
    combinations contain more than two items. So with the previous task list and disallow ['ABC'] we want to first keep
    'A' and so remove 'B' and 'C', then keep 'B' and remove 'A' and 'C' and so on. If there is more than one element in
    disallow we need to form the product first - so ['AB', 'CD'] gives four pairs to remove AC AD BC BD.
    """
    lists = []
    if disallow and len(disallow) > 0 and disallow[0] != '':
        ctk = list(itertools.product(*disallow))
#        print "combinations to keep %s " % str(ctk)
        ctr = []
        for i in range(len(ctk)):
            tk = ctk[i]
            td = disallow
#            print "tk %s td %s" % (tk, td)
            tr = ()
            for j in range(len(tk)):
                tr = tr + tuple(td[j].replace(tk[j], ''))
#            print "tr %s td %s" % (tr, td)
            ctr.append(tr)
#        print "combinations to remove %s " % str(ctr)
        for group in ctr:
#            print "REMOVING %s" % str(group)
            factorsClone = list(factors)
            for d in group:
                factorsClone.remove(d)
#            print "APPENDING %s\n" % str(factorsClone)
            lists.append(factorsClone)
    else:
        lists.append(factors)
    return lists


def generate(toCall, task_count, interface_count, shuffle, task_disallow, interface_disallow):

    tasks = [chr(i+65) for i in range(task_count)] 
    interfaces = [chr(i+49) for i in range(interface_count)] 

    taskLists = constructLists(tasks, task_disallow)
    interfaceLists = constructLists(interfaces, interface_disallow)

    toDoList = []
    for i in range(len(taskLists)):
        for j in range(len(interfaceLists)):
            toDoList = toDoList + globals()[toCall](taskLists[i], interfaceLists[j])

    if shuffle:
        random.shuffle(toDoList)

    return toDoList

def calculate(toCall, task_count, interface_count, shuffle, task_disallow, interface_disallow):

    tasks = [chr(i+65) for i in range(task_count)] 
    interfaces = [chr(i+49) for i in range(interface_count)] 

    taskLists = constructLists(tasks, task_disallow)
    interfaceLists = constructLists(interfaces, interface_disallow)

    count = 0;
    for taskList in taskLists:
        for interfaceList in interfaceLists:
            print "taskList %s interfaceList %s" % (str(taskList), str(interfaceList))
            print "adding %d!" % (len(taskList) * len(interfaceList))
            count = count + math.factorial(len(taskList) * len(interfaceList))

    return count
