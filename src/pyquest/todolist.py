import itertools
import math
import random

# within means each user must do all
# between means that between them all users must do all

# within-within
def ww(tasks, interfaces, taskRestores, interfaceRestores, generate):
    if generate:
        combinations = []
        for task in tasks:
            for interface in interfaces:
                combinations.append((task, interface))
        print "Combinations before %s" % str(combinations)
        rawpermutations = [list(i) for i in itertools.permutations(combinations)]

        permutations = []

        if len(taskRestores) > 0:
            ac = []
            for tr in taskRestores:
                for interface in interfaces:
                    ac.append((tr, interface))
            print "TR additional combinations before %s" % str(ac)
            ap = [list(i) for i in itertools.permutations(ac)]
            print "TR additional permutations before %s" % str(ap)
#            permutations = []
# THIS IS NOT SUFFICIENT, for example if a is [[(A,1), (A,2)], [(C,1), (C,2)]] and p is [[(B,1), (B,2)]] then
# [(A,1), (A,2), (C,1), (C,2), (B,1), (B,2)] is allowed but so also is
# [(A,1), (A,2), (C,1), (B,1), (C,2), (B,2)]
# and [(A,1), (A,2), (B,1), (B,2), (C,1), (C,2)] will have been calculated by other means
# I think perhaps the whole scheme is wrong - the within-within allows intermingling of the partitions.
            for a in ap:
                for p in rawpermutations:
                    permutations.append(a + p)

        elif len(interfaceRestores) > 0:
            ac = []
            for t in tasks:
                for ir in interfaceRestores:
                    ac.append((t, ir))
            print "IR additional combinations before %s" % str(ac)
            ap = [list(i) for i in itertools.permutations(ac)]
            print "IR additional permutations before %s" % str(ap)
#            permutations = []
            for a in ap:
                for p in rawpermutations:
                    permutations.append(a + p)
        else:
            permutations = rawpermutations
    else:
        permutations = math.factorial(len(tasks) * len(interfaces))
        if len(taskRestores) > 0:
            permutations = math.factorial(len(taskRestores) * len(interfaces)) * permutations
        elif len(interfaceRestores) > 0:
            permutations = math.factorial(len(tasks) * len(interfaceRestores)) * permutations

    return permutations

# within-between
def wb(tasks, interfaces, taskRestores, interfaceRestores, generate):
    if generate:
        permutations = []
        for interface in interfaces:
            combinations = []
            for task in tasks:
                combinations.append((taskRestores + task, interface))
            print "Combinations before %s" % str(combinations)
            permutations = permutations + [list(i) for i in itertools.permutations(combinations)]
    else:
        permutations = math.factorial(len(tasks)) * len(interfaces)

    return permutations;

# between-within
def bw(tasks, interfaces, taskRestores, interfaceRestores, generate):
    if generate:
        permutations = []
        for task in tasks:
            combinations = []
            for interface in interfaces:
                combinations.append((taskRestores + task, interface))
            print "Combinations before %s" % str(combinations)
            permutations = permutations + [list(i) for i in itertools.permutations(combinations)]
    else:
        permutations = len(tasks) * math.factorial(len(interfaces))

    return permutations

# between-between
def bb(tasks, interfaces, taskRestores, interfaceRestores, generate):
    if generate:                                                  
        permutations = []
        for task in tasks:
            for interface in interfaces:
                permutations.append([(taskRestores + task, interface)])
    else:
        permutations = len(tasks) * len(interfaces)

    return permutations

def listsWithDisallow(factors, disallow):
    """ Constructs the sublists of combinations needed according to the restrictions passed in. So, for example, if passed 
    ['A', 'B', 'C', 'D', 'E'] as factors and ['AB'] as disallow it will return the two lists ['A', 'C', 'D', 'E']
    and ['B', 'C', 'D', 'E']. It is done as 'to keep' and then 'to remove' in order to handle cases where disallowed 
    combinations contain more than two items. So with the previous task list and disallow ['ABC'] we want to first keep
    'A' and so remove 'B' and 'C', then keep 'B' and remove 'A' and 'C' and so on. If there is more than one element in
    disallow we need to form the product first - so ['AB', 'CD'] gives four pairs to remove AC AD BC BD.
    """
    lists = []
    restores = []
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
        restores.append([])

    return (restores, lists)

def listsWithOrder(factors, order):
    """ If passed factors ['A','B', 'C'] and order ['AB'] then we want only those permutations of ABC which have A before B. This
    can be done recursively by partitioning the factors. We need ['A'] plus the permutations of ['B', 'C'] AND ['C'] plus the result of
    applying the same process again to ['A', 'B']. The result of this second process in ['A'] plus permutations of ['B']. This function
    returns two lists and the recursion has only to define how to add them together - restore['C'] + {restore['A'] + permute['B']} equals
    restore ['C, A'] + permute ['B']. So the total outcome for listsWithOrder(['A', 'B', 'C'], ['AB']) will be:

    restore[0] = ['A'] permute[0] = ['B', 'C']
    restore[1] = ['C', 'A'] permute[1] = ['B']

    and we compute the final permutations as ['A'] + ['B', 'C'] = ['A', 'B', 'C']
                                             ['A'] + ['C', 'B'] = ['A', 'C', 'B']
                                             ['C', 'A'] + ['B'] = ['C', 'A', 'B']
    """
    lists = []
    restores = []
    for f in factors:
        if f == order[0][0]:
            lists.append(factors[1:])
            restores.append([f])
        elif f != order[0][1]:
            factorsClone = list(factors)
            factorsClone.remove(f)
            reply = listsWithOrder(factorsClone, order)
            for i in range(len(reply[0])):
                restores.append([f] + reply[0][i])
                lists.append(reply[1][i])
    return (restores, lists)


def constructLists(factors, disallow, order):
    restores = []
    lists = []
    if disallow and len(disallow) > 0 and disallow[0] != '':
        reply = listsWithDisallow(factors, disallow)
        restores = reply[0]
        lists = reply[1]
    elif order and len(order) > 0 and order[0] != '':
        reply = listsWithOrder(factors, order)
        restores = reply[0]
        lists = reply[1]
    else:
        lists.append(factors)
        restores.append([])

    for i in range(len(restores)):
        print "restore %s perm %s" %(str(restores[i]), str(lists[i]))
    return (restores, lists)

def getPermutations(worb, task_count, interface_count, shuffle, task_disallow, interface_disallow, generate, task_order, interface_order):

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

    iOrder = []
    for bit in interface_order.split(','):
        iOrder.append(bit)

    reply = constructLists(tasks, tDisallow, tOrder)
    taskRestores = reply[0]
    taskLists = reply[1]
    reply = constructLists(interfaces, iDisallow, iOrder)
    interfaceRestores = reply[0]
    interfaceLists = reply[1]

    if generate:
        toDoList = []
    else:
        toDoList = 0

    for i in range(len(taskLists)):
        for j in range(len(interfaceLists)):
                toDoList = toDoList + globals()[worb](taskLists[i], interfaceLists[j], taskRestores[i], interfaceRestores[j], generate)

    if generate and shuffle:
        random.shuffle(toDoList)

    # First attemp BFI 
    # get the two tasks from 'tOrder'
    # if tOrder and len(tOrder) > 0 and tOrder[0] != '':
    #     for order in tOrder:
    #         if generate:
    #             order = order[::-1]

    #             toRemove = []
    #             for i in range(len(toDoList)):

    #                 if remove(toDoList[i], 0, order, len(toDoList[i])):
    #                     toRemove.append(i)

    #             toRemove.reverse()
    #             print "reversed toRemove is %s" % str(toRemove)

    #             for i in toRemove:
    #                 del toDoList[i]
                    
    return toDoList

def remove(perm, start, searchFor, end):
    for j in range(start, end):
        if perm[j][0] == searchFor[0]:
            if len(searchFor) > 1:
                return remove(perm, j, searchFor[1:], end)
            else:
                return True
    return False;
