import itertools
import math
import random

# within means each user must do all
# between means that between them all users must do all

# within-within
def ww(tasks, interfaces, generate):
    if generate:
        combinations = []
        for task in tasks:
            for interface in interfaces:
                combinations.append((task, interface))
        print "Combinations before %s" % str(combinations)
        permutations = [list(i) for i in itertools.permutations(combinations)]
    else:
        permutations = math.factorial(len(tasks) * len(interfaces))

    return permutations

# within-between
def wb(tasks, interfaces, generate):
    if generate:
        permutations = []
        for interface in interfaces:
            combinations = []
            for task in tasks:
                combinations.append((task, interface))
            print "Combinations before %s" % str(combinations)
            permutations = permutations + [list(i) for i in itertools.permutations(combinations)]
    else:
        permutations = math.factorial(len(tasks)) * len(interfaces)

    return permutations;

# between-within
def bw(tasks, interfaces, generate):
    if generate:
        permutations = []
        for task in tasks:
            combinations = []
            for interface in interfaces:
                combinations.append((task, interface))
            print "Combinations before %s" % str(combinations)
            permutations = permutations + [list(i) for i in itertools.permutations(combinations)]
    else:
        permutations = len(tasks) * math.factorial(len(interfaces))

    return permutations

# between-between
def bb(tasks, interfaces, generate):
    if generate:                                                  
        permutations = []
        for task in tasks:
            for interface in interfaces:
                permutations.append([(task, interface)])
    else:
        permutations = len(tasks) * len(interfaces)

    return permutations

def constructLists(factors, disallow, order):
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

def getPermutations(worb, task_count, interface_count, shuffle, task_disallow, interface_disallow, generate, task_order):

    tasks = [chr(i+65) for i in range(int(task_count))] 
    interfaces = [chr(i+49) for i in range(int(interface_count))] 
    
    tDisallow = []
    if worb[0] == 'w' and task_disallow:
        for bit in task_disallow.split(','):
            tDisallow.append(bit)
    iDisallow = [] 
    if worb[1] == 'w' and interface_disallow:
        for bit in interface_disallow.split(','):
            iDisallow.append(bit)

    tOrder = []
    for bit in task_order.split(','):
        tOrder.append(bit)

    taskLists = constructLists(tasks, tDisallow, tOrder)
    interfaceLists = constructLists(interfaces, iDisallow, None)

    if generate:
        toDoList = []
    else:
        toDoList = 0

    for i in range(len(taskLists)):
        for j in range(len(interfaceLists)):
            toDoList = toDoList + globals()[worb](taskLists[i], interfaceLists[j], generate)

    if generate and shuffle:
        random.shuffle(toDoList)

    # First attemp BFI 
    # get the two tasks from 'tOrder'
    if tOrder and len(tOrder) > 0 and tOrder[0] != '':
        for order in tOrder:
            if generate:
                order = order[::-1]

                toRemove = []
                for i in range(len(toDoList)):

                    if remove(toDoList[i], 0, order, len(toDoList[i])):
                        toRemove.append(i)

                toRemove.reverse()
                print "reversed toRemove is %s" % str(toRemove)

                for i in toRemove:
                    del toDoList[i]
            else:
                toDoList = toDoList / 2
                    
    return toDoList

def remove(perm, start, searchFor, end):
    for j in range(start, end):
        if perm[j][0] == searchFor[0]:
            if len(searchFor) > 1:
                return remove(perm, j, searchFor[1:], end)
            else:
                return True
    return False;
