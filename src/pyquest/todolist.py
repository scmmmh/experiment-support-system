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

def getPermutations(worb, task_count, interface_count, shuffle, task_disallow, interface_disallow, generate, tOrder):

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

    taskLists = constructLists(tasks, tDisallow)
    interfaceLists = constructLists(interfaces, iDisallow)

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
    if generate and tOrder and len(tOrder) > 0:
        tOrder = tOrder[::-1]

        toRemove = []
        for i in range(len(toDoList)):
        # # search for a tuple that begins with tTwo
        #     for j in range(0, len(toDoList[i])):
        #         if toDoList[i][j][0] == tOrder[0]:
        # # search from the finding point for a tuple that starts with tOne, if there is one then
        #             for k in range(j, len(toDoList[i])):
        #                 if toDoList[i][k][0] == tOrder[1]:
        #                     # remove this permutation from the list
        #                     toRemove.append(i)
        #                     break

            if recur(toDoList[i], 0, tOrder, len(toDoList[i])):
                toRemove.append(i)

        toRemove.reverse()
        print "reversed toRemove is %s" % str(toRemove)

        for i in toRemove:
            del toDoList[i]

    return toDoList

def recur(perm, start, searchFor, end):
    for j in range(start, end):
        if perm[j][0] == searchFor[0]:
            if len(searchFor) > 1:
                return recur(perm, j, searchFor[1:], end)
            else:
                return True
    return False;
