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
def generate_ww(tasks, interfaces, tDisallow, iDisallow):

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
def generate_wb(tasks, interfaces, tDisallow, iDisallow):

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
def generate_bw(tasks, interfaces, tDisallow, iDisallow):

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
def generate_bb(tasks, interfaces, tDisallow, iDisallow):
    combinations = []
    for task in tasks:
        for interface in interfaces:
            combinations.append([(task, interface)])
    return combinations


def generate_combinations(worb, task_count, interface_count, task_disallow, interface_disallow):
    tasks = [chr(i+65) for i in range(int(task_count))] 
    interfaces = [chr(i+49) for i in range(int(interface_count))] 

    tDisallow = [' ']
    if worb[0] == 'w' and task_disallow:
        tDisallow = [bit for bit in task_disallow.split(',')]

    iDisallow = [' ']
    if worb[1] == 'w' and interface_disallow:
        iDisallow = [bit for bit in interface_disallow.split(',')]


    combinations = globals()['generate_' + worb](tasks, interfaces, tDisallow, iDisallow)
    
    return combinations

def getPermutations(worb, task_count, interface_count, shuffle, task_disallow, interface_disallow, task_order, interface_order):
    
    combinations = generate_combinations(worb, task_count, interface_count, task_disallow, interface_disallow)

    tOrder = [' ']
    if worb[0] == 'w' and task_order:
        tOrder = [bit for bit in task_order.split(',')]

    iOrder = [' ']
    if worb[1] == 'w' and interface_order:
        iOrder = [bit for bit in interface_order.split(',')]


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

def recur(comb, order, pad):
    s = str(comb)
#    print "%sSTARTING %s" % (pad, s)
    count = 0
    if order != ' ' and s.find(order[0]) != -1 and s.find(order[1]) != 1:
        for i in comb:
            if len(comb)== 0:
                break
            subcomb = list(comb)
            subcomb.remove(i)
#            print "%sITEM %s SUBCOMB is %s" %(pad, str(i), str(subcomb))
            if str(i).find(order[0]) != -1:
                if str(subcomb).find(order[0]) == -1:
                    count = count + math.factorial(len(subcomb))
#                    print "%sCOUNT is now %d" % (pad, count)
                else:
                    count = count + recur(subcomb, order, pad + '  ')
#                    print "%sCOUNT is now %d" % (pad, count)
            elif str(i).find(order[1]) != -1:
                pass
            else:
                count = count + recur(subcomb, order, pad + '  ')
#                print "%sCOUNT is now %d" % (pad, count)
#    print "%sRETURNING %d for %s" % (pad, count, s)
    return count

def countPermutations(worb, task_count, interface_count, shuffle, task_disallow, interface_disallow, task_order, interface_order):

    combinations = generate_combinations(worb, task_count, interface_count, task_disallow, interface_disallow)

    tOrder = [' ']
    if worb[0] == 'w' and task_order:
        tOrder = [bit for bit in task_order.split(',')]

    iOrder = [' ']
    if worb[1] == 'w' and interface_order:
        iOrder = [bit for bit in interface_order.split(',')]

    permcount = 0

    if tOrder[0] == ' ':
        if iOrder[0] == ' ':
            orders = None
            for subc in combinations:
                permcount = permcount + math.factorial(len(subc))
        else:
            orders = iOrder
    else:
        if iOrder[0] == ' ':
            orders = tOrder
        else:
            orders = None

    if orders:
        for subc in combinations:
            comb = list(subc)
            for order in orders:
                permcount = permcount + recur(comb, order, ' ')

    return permcount

def remove(perm, start, searchFor, end):
    for j in range(start, end):
        if perm[j][0] == searchFor[0]:
            if len(searchFor) > 1:
                return remove(perm, j, searchFor[1:], end)
            else:
                return True
    return False;
