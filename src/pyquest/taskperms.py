import itertools
import math
import random



# within means each user must do all
# between means that between them all users must do all

# within-within
def generate_ww(tasks, interfaces, tDisallow, iDisallow):
    """ Generates the combinations for the within-within situation. 

    :param tasks: the list of tasks
    :param interfaces: the list of interfaces
    :param tDisallow: the list of task pairs to be excluded 
    :param iDisallow: the list of interface pairs to be excluded (not used but present for consistency of method signature)

    :return a list of the possible combinations of tasks and interfaces to be permuted
    """

    task_exclusion_combinations = itertools.product(*tDisallow)
    # task_exclusion_combinations will now be a set of tuples, if exclusions is ['AB']
    # we get ('A',) and ('B',), if exclusions is ['AB', 'CD'] we get (A,C), (A,D),
    #(B,C), (B,D). We need to ALLOW combinations which miss out each of these exclusions
    # in turn. The same is done for the interface exclusions inside the loop. The within-between
    # and between-withing functions need 

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

def generate_wb(tasks, interfaces, tDisallow, iDisallow):
    """ Generates the combinations for the within-between situation. The interface exclusions are not used. The user interface does
    not allow them to be specified for 'between' factors because they would be the same as just reducing the number of factors.

    :param tasks: the list of tasks
    :param interfaces: the list of interfaces
    :param tDisallow: the list of task pairs to be excluded 
    :param iDisallow: the list of interface pairs to be excluded (not used but present for consistency of method signature)

    :return a list of the possible combinations of tasks and interfaces to be permuted
    """
    # For this situation we need to construct the task_exclusion_combinations but not the interface_exclusion_combinations.
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

def generate_bw(tasks, interfaces, tDisallow, iDisallow):
    """ Generates the combinations for the between-within situation. The task exclusions are not used. The user interface does
    not allow them to be specified for 'between' factors because they would be the same as just reducing the number of factors.

    :param tasks: the list of tasks
    :param interfaces: the list of interfaces
    :param tDisallow: the list of task pairs to be excluded (not used but present for consistency of method signature)
    :param iDisallow: the list of interface pairs to be excluded

    :return a list of the possible combinations of tasks and interfaces to be permuted
    """
    # For this situation we need to construct the interface_exclusion_combinations but not the task_exclusion_combinations.
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

def generate_bb(tasks, interfaces, tDisallow, iDisallow):
    """ Generates the combinations for the between-between situation. The exclusions are not used. The user interface does
    not allow them to be specified for 'between' factors because they would be the same as just reducing the number of factors.

    :param tasks: the list of tasks
    :param interfaces: the list of interfaces
    :param tDisallow: the list of task pairs to be excluded (not used but present for consistency of method signature)
    :param iDisallow: the list of interface pairs to be excluded (not used but present for consistency of method signature)

    :return a list of the possible combinations of tasks and interfaces permuted
    """
    combinations = []
    for task in tasks:
        for interface in interfaces:
            combinations.append([(task, interface)])
    return combinations


def generate_combinations(worb, task_count, interface_count, task_disallow, interface_disallow):
    """
 
    :param worb:
    :param task_count:
    :param interface_count:
    :param task_disallow:
    :param interface_disallow:
    :return
    """
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

def getPermutations(worb, task_count, interface_count, task_disallow, interface_disallow, task_order, interface_order):
    """ Gets the permutations for the given configuration.

    :param worb: the within-between specification ('ww', 'wb', 'bw' or 'bb')
    :param task_count: the number of tasks
    :param interface_count: the number of interfaces
    :param task_disallow: task combinations to exclude
    :param interface_disallow: interface combinations to exclude
    :param task_order: task orders to enforce
    :param interface_order: interface orders to enforce
    :return the number of permutations this configuration will generate
    """
    
    combinations = generate_combinations(worb, task_count, interface_count, task_disallow, interface_disallow)

    tOrder = [' ']
    if worb[0] == 'w' and task_order:
        tOrder = [bit for bit in task_order.split(',')]

    iOrder = [' ']
    if worb[1] == 'w' and interface_order:
        iOrder = [bit for bit in interface_order.split(',')]


    def orderFactors(factor, order):
        """ Checks whether the given 'factor' contain the combination 'order' in the correct order. 
        If the 'order' contains more than two elements it is ignored and the function returns True. 

        :param factor: is a permutation as a string, for example "[('B', '1'), ('A', '2')]"
        :param order: is an order which must be maintained, for example 'AB'. 

        :return True if the 'factor' contains the elements of 'order' in the right order
        """

        if len(order) != 2:
            return True

        #FIXME: this does not behave correctly if either order[0] or order[1] is not present!
        return  str(factor).rfind(order[0]) < str(factor).find(order[1])

    def order_func(i):
	"""
 
	:param i:
	:return
	"""
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
    """
 
    :param comb:
    :param order:
    :param pad:
    :return
    """
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

def countPermutations(worb, task_count, interface_count, task_disallow, interface_disallow, task_order, interface_order):
    """ Counts the number of permutations there will be for the given configuration.
 
    :param worb: the within-between specification ('ww', 'wb', 'bw' or 'bb')
    :param task_count: the number of tasks
    :param interface_count: the number of interfaces
    :param task_disallow: task combinations to exclude
    :param interface_disallow: interface combinations to exclude
    :param task_order: task orders to enforce
    :param interface_order: interface orders to enforce
    :return the number of permutations this configuration will generate
    """

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
    """
 
    :param perm:
    :param start:
    :param searchFor:
    :param end:
    :return
    """
    for j in range(start, end):
        if perm[j][0] == searchFor[0]:
            if len(searchFor) > 1:
                return remove(perm, j, searchFor[1:], end)
            else:
                return True
    return False;
