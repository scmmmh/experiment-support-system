import itertools
import math

def generate_ww(tasks, interfaces, tDisallow, iDisallow):
    """ Generates the combinations for the within-within situation. The basic procedure is still as described for generate_wb 
    but here we must make subcombinations where every possible pair of task exclusions is combined with every possible
    pair of interface exclusions. So if we have tasks ['A', 'B', 'C', 'D'], interfaces ['1', '2', '3'], tDisallow['AB', 'CD'] and
    iDisallow['12'] then we need:
                  (all possible combinations with 'A' and 'C' excluded from tasks and '1' excluded from interfaces) +
                  (all possible combinations with 'A' and 'D' excluded from tasks and '1' excluded from interfaces) +
                  (all possible combinations with 'B' and 'C' excluded from tasks and '1' excluded from interfaces) +
                  (all possible combinations with 'B' and 'D' excluded from tasks and '1' excluded from interfaces) +
                  ... the same task exclusions with '2' excluded from interfaces.

    :param tasks: the list of tasks
    :param interfaces: the list of interfaces
    :param tDisallow: the list of task pairs to be excluded 
    :param iDisallow: the list of interface pairs 

    :return a list of the possible combinations of tasks and interfaces to be permuted
    """

    task_exclusion_combinations = itertools.product(*tDisallow)

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
    The procedure is best described by example. If the tasks are ['A', 'B', 'C', 'D'] and tDisallow is ['AB'] then instead of 
    all possible combinations of 'ABCD' we need: 
                  (all possible combinations with 'A' excluded) + 
                  (all possible combinations with 'B' excluded).
    When tDisallow has two disallowed pairs ['AB', 'CD'] then we need:
                  (all possible combinations with 'A' and 'C' excluded) +
                  (all possible combinations with 'A' and 'D' excluded) +
                  (all possible combinations with 'B' and 'C' excluded) +
                  (all possible combinations wiht 'B' and 'D' excluded)
    The itertools product method with *tDisallow as parameter produces the values we need to exclude ('A', 'B') in the first example
    ('AC', 'AD', 'BC', 'BD') in the second. With each excluded we make a subcombination of tuples of the remaining tasks and the interfaces. 

    :param tasks: the list of tasks
    :param interfaces: the list of interfaces
    :param tDisallow: the list of task pairs to be excluded 
    :param iDisallow: the list of interface pairs to be excluded (not used but present for consistency of method signature)

    :return a list of the possible combinations of tasks and interfaces to be permuted
    """
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
    The procedure here is the same as in generate_wb but with interface and task exchanged.

    :param tasks: the list of tasks
    :param interfaces: the list of interfaces
    :param tDisallow: the list of task pairs to be excluded (not used but present for consistency of method signature)
    :param iDisallow: the list of interface pairs to be excluded

    :return a list of the possible combinations of tasks and interfaces to be permuted
    """
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
    This is the simplest of the four worbs - each combination consists of only one (task, interface) tuple.

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


def generate_combinations(worb, tasks, interfaces, task_disallow, interface_disallow):
    """ Generates the allowed combinations of task and interface. This function only prepares the
    task and interface lists and the combinations to be disallowed. The actual procedure differs
    according to the within-between values and so there is a separate function for each of the
    four possibilities. 
 
    :param worb: the within-between specification ('ww', 'wb', 'bw' or 'bb')
    :param task_count: the number of tasks
    :param interface_count: the number of interfaces
    :param task_disallow: task combinations to exclude
    :param interface_disallow: interface combinations to exclude
    :return a list of lists of the combinations which must be permuted
    """
#    tasks = [chr(i+65) for i in range(int(task_count))] 
#    interfaces = [chr(i+49) for i in range(int(interface_count))] 

#    tDisallow = [' ']
#    if worb[0] == 'w' and task_disallow:
#        tDisallow = [bit for bit in task_disallow.split(',')]

    # iDisallow = [' ']
    # if worb[1] == 'w' and interface_disallow:
    #     iDisallow = [bit for bit in interface_disallow.split(',')]

    combinations = globals()['generate_' + worb](tasks, interfaces, task_disallow, interface_disallow)

    return combinations

def generate_permutations(worb, tOrder, iOrder, combinations):
    """Generates the permutations for the given combinations. This is done by using itertools to generate the permutations
    for each subcombination and filtering through a function which determines whether the required ordering is maintained.

    :param worb: the within-between specification ('ww', 'wb', 'bw' or 'bb')
    :param task_order: task orders to enforce
    :param interface_order: interface orders to enforce
    :param combinations: the combinations which need to be permuted
    :return the number of permutations this configuration will generate
    """
    
    # tOrder = [' ']
    # if worb[0] == 'w' and task_order:
    #     tOrder = [bit for bit in task_order.split(',')]

    # iOrder = [' ']
    # if worb[1] == 'w' and interface_order:
    #     iOrder = [bit for bit in interface_order.split(',')]


    def orderFactors(factor, order):
        """ Checks whether the given 'factor' contain the combination 'order' in the correct order. 
        If the 'order' contains more than two elements it is ignored and the function returns True. 

        :param factor: is a permutation as a string, for example "[('B', '1'), ('A', '2')]"
        :param order: is an order which must be maintained, for example 'AB'. 

        :return True if the 'factor' contains the elements of 'order' in the right order
        """

        if len(order) != 2:
            return True

        rtrn = factor.rfind(order[0]) == -1 or factor.find(order[1]) == -1 or  factor.rfind(order[0]) < factor.find(order[1])
        return rtrn

    def order_func(i):
	""" Set as the filter function on the permutation generation. Applies the factor orderings
        to the permutation.
 
	:param i: will be each permutation in turn
	:return True if all the factors are in the required order, false otherwise
	"""
        rtrn = True;
        factor = str(i)
        for order in tOrder:
            rtrn = rtrn and orderFactors(factor, order)
        for order in iOrder:
            rtrn = rtrn and orderFactors(factor, order)
        return rtrn
    
    permutations = [] 
    for subc in combinations:
        permutations = permutations + [list(i) for i in itertools.ifilter(order_func, itertools.permutations(subc))]

    return permutations

def getPermutations(worb, tasks, interfaces, tExclude, iExclude, tOrder, iOrder, generate):
    """ Gets the actual permutations or counts how many permutations there will be for the given configuration. There are two
    stages. The first stage is to generate the allowed combinations of tasks and interfaces. The second stage is either to generate
    the actual permutations or to count how many there will be. 

    :param worb: the within-between specification ('ww', 'wb', 'bw' or 'bb')
    :param task_count: the number of tasks
    :param interface_count: the number of interfaces
    :param task_disallow: task combinations to exclude
    :param interface_disallow: interface combinations to exclude
    :param task_order: task orders to enforce
    :param interface_order: interface orders to enforce
    :param generate: if True return permutations, else return number of permutation
    :return either a list of permutations or a count of how many permutations there will be
    """
    combinations = []

    if len(tasks) > 0 and len(interfaces) > 0:
        tasks = tasks.split(',')
        interfaces = interfaces.split(',')
        combinations = generate_combinations(worb, tasks, interfaces, tExclude, iExclude)

    if generate:
        permutations = generate_permutations(worb, tOrder, iOrder, combinations)
    else:
        permutations = count_permutations(worb, tOrder, iOrder, combinations)

    return permutations


def count_subcombination(combination, order):
    """ Counts how many permutations the given combination will produce with the given order constraint. This is done by
    partitioning the combination and calling this method recursively. For example with tasks ['A', 'B', 'C'] and 
    interfaces ['1', '2'] and no exclusion constraints then combinations will be:
            [[('A', '1'), ('A', '2'), ('B', '1'), ('B', '2'), ('C', '1'), ('C', '2')]]
    a list with a single subcombination of 6 tuples. If there were no ordering constraints this would generate 6! = 720 
    permutations. If we have the ordering constraint 'AB' then we can count the permutations by partitioning - 
             remove the ('A', '1') and the permutations of [other five items in the list] which pass (by calling this recursively)
       plus  remove the ('A', '2') and the permutations of [other five items in the list] which pass (by calling this recursively)
       plus  NONE from those that have ('B', '1') at the start
       plus  NONE from those that have ('B', '2') at the start
       and so on
 
    :param combination: the combination to deal with
    :param order: the ordering constraint being considered
    :return the number of permutations this 
    """
    s = str(combination)
    count = 0
    # if the combination contains both of the items of order then processing is necessary
    if s.find(order[0]) != -1 and s.find(order[1]) != -1:
        for item in combination:
            # The recursion ends when there are no items to remove from combination
            if len(combination)== 0:
                break
            subcombination = list(combination)
            # subcombination is the current combination with item remove
            subcombination.remove(item)
            if str(item).find(order[0]) != -1:
                if str(subcombination).find(order[0]) == -1:
                    # order[0] is in the first item but not in the rest 
                    # so all of the permutations of subcombination will be valid
                    count = count + math.factorial(len(subcombination))
                else:
                    # order[0] is in the first item and is still in rest. So we have
                    # to recursively call count_subcombination on subcombination
                    count = count + count_subcombination(subcombination, order)
            elif str(item).find(order[1]) != -1:
                # order[1] is in the first item so this combination cannot produce valid permutations 
                pass
            else:
                # Neither order[0] nor order [1] is in the first item so we must repeat the process on the rest of 
                # the combination
                count = count + count_subcombination(subcombination, order)
    # if the combination contains one or neither of the items of order then all its permutations will be valid
    else:
        count = math.factorial(len(combination))
    return count

def count_permutations(worb, tOrder, iOrder, combinations):
    """ Counts how many permutations will be produced by the given combinations. This is actually more difficult than generating the 
    permutations but it takes much less time for large (> 3) values of task_count or interface_count. If there are no order constraints
    then the number of permutations is generated here as the total of the factorials of the lengths of all the subcombinations in 
    combinations. If there are order constraints on both task and interface (only possible in the 'ww' case) then no permutations will
    be produced. In other cases we have to count the subcombinations individually and add them.

    :param worb: the within-between specification ('ww', 'wb', 'bw' or 'bb')
    :param task_order: task orders to enforce
    :param interface_order: interface orders to enforce
    :param combinations: the combinations which need to be permuted
    :return the number of permutations this configuration will generate
    """
    # tOrder = [' ']
    # if worb[0] == 'w' and task_order:
    #     tOrder = [bit for bit in task_order.split(',')]

    # iOrder = [' ']
    # if worb[1] == 'w' and interface_order:
    #     iOrder = [bit for bit in interface_order.split(',')]

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
            subcombination = list(subc)
            # Halving for each two element ordering constraint is true for non-overlapping constraints. Overlapping
            # constraints will produce fewer permutations so this is an upper bound.
            rf = 1
            for order in orders:
                if order != ' ' and (str(subc).find(order[0]) != -1) and (str(subc).find(order[1]) != -1):
                    rf = rf * 2
            permcount = permcount + math.factorial(len(subc)) / rf

    return permcount
