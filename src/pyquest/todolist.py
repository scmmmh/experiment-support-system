import itertools
import math
import random

def orderFactors(factor, order):

    if len(order) != 2:
        return True

    a = order[0]
    b = order[1]
    lasta = str(factor).rfind(a)
    firstb = str(factor).find(b)
    return lasta < firstb

# within means each user must do all
# between means that between them all users must do all

# within-within
def generate_ww(tasks, interfaces, tDisallow, iDisallow, tOrder, iOrder):

    task_exclusion_combinations = itertools.product(*tDisallow)
#task_exclusion_combinations will now be a set of tuples, if exclusions is ['AB']
#we get ('A',) and ('B',), if exclusions is ['AB', 'CD'] we get (A,C), (A,D),
#(B,C), (B,D). We need to allow combinations which miss out each of these exclusions
# in turn. 
    combinations = []
    for task_exclusion in task_exclusion_combinations:
        interface_exclusion_combinations = itertools.product(*iDisallow)
        for interface_exclusion in interface_exclusion_combinations:
            subcombination = []
            for task in tasks:
                if task not in task_exclusion:
                    for interface in interfaces:
                        if interface not in interface_exclusion:
                            subcombination.append((task, interface))
            combinations.append(subcombination)

    return combinations

# within-between
def generate_wb(tasks, interfaces, tDisallow, iDisallow, tOrder, iOrder):

    combinations = []
    for interface in interfaces:
        task_exclusion_combinations = itertools.product(*tDisallow)
        for task_exclusion in task_exclusion_combinations:
            subcombination = []
            for task in tasks:
                if task not in task_exclusion:
                    subcombination.append((task, interface))
            combinations.append(subcombination)

    return combinations

# between-within
def generate_bw(tasks, interfaces, tDisallow, iDisallow, tOrder, iOrder):

    combinations = []
    for task in tasks:
        interface_exclusion_combinations = itertools.product(*iDisallow)
        for interface_exclusion in interface_exclusion_combinations:
            subcombination = []
            for interface in interfaces:
                if interface not in interface_exclusion:
                    subcombination.append((task, interface))
            combinations.append(subcombination)

    return combinations

# between-between
def generate_bb(tasks, interfaces, tDisallow, iDisallow, tOrder, iOrder):
    combinations = []
    for task in tasks:
        for interface in interfaces:
            combinations.append([(task, interface)])
    return combinations

# within-within
def count_ww(tasks, interfaces, taskRestores, interfaceRestores, generate):

    permutations = math.factorial(len(tasks) * len(interfaces))
    if len(taskRestores) > 0:
        if len(interfaceRestores) > 0:
            permutations = 0
        else:
            permutations = math.factorial(len(taskRestores) * len(interfaces)) * permutations
    elif len(interfaceRestores) > 0:
        permutations = math.factorial(len(tasks) * len(interfaceRestores)) * permutations

    return permutations

# within-between
def count_wb(tasks, interfaces, taskRestores, interfaceRestores, generate):
    if generate:
        permutations = []
        for interface in interfaces:
            combinations = []
            for task in tasks:
                combinations.append((taskRestores + task, interface))
            print "Combinations before %s" % str(combinations)
            permutations = permutations + [list(i) for i in itertools.permutations(combinations)]
    else:
        permutations = len(interfaces) * math.factorial(len(tasks) * len(interfaces))

    return permutations;

# between-within
def count_bw(tasks, interfaces, taskRestores, interfaceRestores, generate):
    permutations = len(tasks) * math.factorial(len(interfaces))
    return permutations

# between-between
def count_bb(tasks, interfaces, taskRestores, interfaceRestores, generate):
    return len(tasks) * len(interfaces)

# def listsWithDisallow(factors, disallow):
#     """ Constructs the sublists of combinations needed according to the restrictions passed in. So, for example, if passed 
#     ['A', 'B', 'C', 'D', 'E'] as factors and ['AB'] as disallow it will return the two lists ['A', 'C', 'D', 'E']
#     and ['B', 'C', 'D', 'E']. It is done as 'to keep' and then 'to remove' in order to handle cases where disallowed 
#     combinations contain more than two items. So with the previous task list and disallow ['ABC'] we want to first keep
#     'A' and so remove 'B' and 'C', then keep 'B' and remove 'A' and 'C' and so on. If there is more than one element in
#     disallow we need to form the product first - so ['AB', 'CD'] gives four pairs to remove AC AD BC BD.
#     """
#     lists = []
#     restores = []
#     ctk = list(itertools.product(*disallow))
# #        print "combinations to keep %s " % str(ctk)
#     ctr = []
#     for i in range(len(ctk)):
#         tk = ctk[i]
#         td = disallow
# #            print "tk %s td %s" % (tk, td)
#         tr = ()
#         for j in range(len(tk)):
#             tr = tr + tuple(td[j].replace(tk[j], ''))
# #            print "tr %s td %s" % (tr, td)
#         ctr.append(tr)
# #        print "combinations to remove %s " % str(ctr)
#     for group in ctr:
# #            print "REMOVING %s" % str(group)
#         factorsClone = list(factors)
#         for d in group:
#             factorsClone.remove(d)
# #            print "APPENDING %s\n" % str(factorsClone)
#         lists.append(factorsClone)
#         restores.append([])

#     return (restores, lists)

# def listsWithOrder(factors, order):
#     """ If passed factors ['A','B', 'C'] and order ['AB'] then we want only those permutations of ABC which have A before B. This
#     can be done recursively by partitioning the factors. We need ['A'] plus the permutations of ['B', 'C'] AND ['C'] plus the result of
#     applying the same process again to ['A', 'B']. The result of this second process in ['A'] plus permutations of ['B']. This function
#     returns two lists and the recursion has only to define how to add them together - restore['C'] + {restore['A'] + permute['B']} equals
#     restore ['C, A'] + permute ['B']. So the total outcome for listsWithOrder(['A', 'B', 'C'], ['AB']) will be:

#     restore[0] = ['A'] permute[0] = ['B', 'C']
#     restore[1] = ['C', 'A'] permute[1] = ['B']

#     and we compute the final permutations as ['A'] + ['B', 'C'] = ['A', 'B', 'C']
#                                              ['A'] + ['C', 'B'] = ['A', 'C', 'B']
#                                              ['C', 'A'] + ['B'] = ['C', 'A', 'B']
#     """
#     lists = []
#     restores = []
#     for f in factors:
#         if f == order[0][0]:
#             lists.append(factors[1:])
#             restores.append([f])
#         elif f != order[0][1]:
#             factorsClone = list(factors)
#             factorsClone.remove(f)
#             reply = listsWithOrder(factorsClone, order)
#             for i in range(len(reply[0])):
#                 restores.append([f] + reply[0][i])
#                 lists.append(reply[1][i])
#     return (restores, lists)


# def constructLists(factors, disallow, order):
#     restores = []
#     lists = []
#     if disallow and len(disallow) > 0 and disallow[0] != '':
#         reply = listsWithDisallow(factors, disallow)
#         restores = reply[0]
#         lists = reply[1]
#     elif order and len(order) > 0 and order[0] != '':
#         reply = listsWithOrder(factors, order)
#         restores = reply[0]
#         lists = reply[1]
#     else:
#         lists.append(factors)
#         restores.append([])

#     for i in range(len(restores)):
#         print "restore %s perm %s" %(str(restores[i]), str(lists[i]))
#     return (restores, lists)

def getPermutations(worb, task_count, interface_count, shuffle, task_disallow, interface_disallow, task_order, interface_order):
    
    tasks = [chr(i+65) for i in range(int(task_count))] 
    interfaces = [chr(i+49) for i in range(int(interface_count))] 

    tDisallow = [' ']
    if worb[0] == 'w' and task_disallow:
        tDisallow = [bit for bit in task_disallow.split(',')]

    iDisallow = [' ']
    if worb[1] == 'w' and interface_disallow:
        iDisallow = [bit for bit in interface_disallow.split(',')]

    tOrder = [' ']
    if worb[0] == 'w' and task_order:
        tOrder = [bit for bit in task_order.split(',')]

    iOrder = [' ']
    if worb[1] == 'w' and interface_order:
        iOrder = [bit for bit in interface_order.split(',')]

    combinations = globals()['generate_' + worb](tasks, interfaces, tDisallow, iDisallow, tOrder, iOrder)

    def order_func(i):
        rtrn = True;
        for order in tOrder:
            rtrn = rtrn and orderFactors(i, order)
        for order in iOrder:
            rtrn = rtrn and orderFactors(i, order)
        return rtrn

    
    permutations = [] 
    for subc in combinations:
        permutations = permutations + [list(i) for i in itertools.ifilter(order_func, itertools.permutations(subc))]

    return permutations

def countPermutations(worb, task_count, interface_count, shuffle, task_disallow, interface_disallow, task_order, interface_order):

    # generate = False
    # tasks = [chr(i+65) for i in range(int(task_count))] 
    # interfaces = [chr(i+49) for i in range(int(interface_count))] 
    
    # tDisallow = []
    # if worb[0] == 'w' and task_disallow:
    #     for bit in task_disallow.split(','):
    #         tDisallow.append(bit)
    # iDisallow = [] 
    # if worb[1] == 'w' and interface_disallow:
    #     for bit in interface_disallow.split(','):
    #         iDisallow.append(bit)

    # tOrder = []
    # for bit in task_order.split(','):
    #     tOrder.append(bit)

    # iOrder = []
    # for bit in interface_order.split(','):
    #     iOrder.append(bit)

    # reply = constructLists(tasks, tDisallow, tOrder)
    # taskRestores = reply[0]
    # taskLists = reply[1]
    # reply = constructLists(interfaces, iDisallow, iOrder)
    # interfaceRestores = reply[0]
    # interfaceLists = reply[1]

    tasks = [chr(i+65) for i in range(int(task_count))] 
    interfaces = [chr(i+49) for i in range(int(interface_count))] 

    tDisallow = [' ']
    if worb[0] == 'w' and task_disallow:
        tDisallow = [bit for bit in task_disallow.split(',')]

    iDisallow = [' ']
    if worb[1] == 'w' and interface_disallow:
        iDisallow = [bit for bit in interface_disallow.split(',')]

    tOrder = [' ']
    if worb[0] == 'w' and task_order:
        tOrder = [bit for bit in task_order.split(',')]

    iOrder = [' ']
    if worb[1] == 'w' and interface_order:
        iOrder = [bit for bit in interface_order.split(',')]

    combinations = globals()['generate_' + worb](tasks, interfaces, tDisallow, iDisallow, tOrder, iOrder)


    # for i in range(len(taskLists)):
    #     for j in range(len(interfaceLists)):
    #             toDoList = toDoList + globals()['count_' + worb](taskLists[i], interfaceLists[j], taskRestores[i], interfaceRestores[j], generate)

    # if generate and shuffle:
    #     random.shuffle(toDoList)

    permcount = 0
    for subc in combinations:
        count = math.factorial(len(subc))
        s = str(subc)
        # it's a bit more complicated than this....
        for order in tOrder:
            if order != ' ' and s.find(order[0]) != -1 and s.find(order[1]) != 1:
                count = count / 2
        permcount = permcount + count

    return permcount

def remove(perm, start, searchFor, end):
    for j in range(start, end):
        if perm[j][0] == searchFor[0]:
            if len(searchFor) > 1:
                return remove(perm, j, searchFor[1:], end)
            else:
                return True
    return False;
