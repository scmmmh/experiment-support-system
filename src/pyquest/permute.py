from  todolist import ToDoListGenerator

def printToDoList(header, toDoList):
    print header
    print "For complete coverage %d participants are needed" % len(toDoList)
    print "Participant\tTo Do"
    participant = 1
    for toDo in toDoList:
        print "%d         \t%s " % (participant, str(toDo))
        participant = participant + 1
    print " "

fullWords = {'w': 'WITHIN', 'b':'BETWEEN', 's':'Shuffled', 'u':'Unshuffled'}

taskCount = int(raw_input('How many tasks?'))
tasks = []
for i in range(taskCount):
    tasks.append(chr(i + 65))
taskWOrB = raw_input('Within or Between tasks?')

interfaceCount = int(raw_input('How many interfaces?'))
interfaces = range(1, interfaceCount + 1)
interfaceWOrB = raw_input('Within or Between interfaces (w or b)?')
toCall = taskWOrB + interfaceWOrB

shuffle = raw_input('Shuffled or un-shuffled (s or u)?')

if shuffle == 's':
    shuffled = True
else:
    shuffled = False

generator = ToDoListGenerator()

title = fullWords[taskWOrB] + ' tasks ' + str(tasks) + ' and ' + fullWords[interfaceWOrB] + ' interfaces ' + str(interfaces) + ' ' + fullWords[shuffle]
toDoList = generator.generate(toCall, tasks, interfaces, shuffled)
printToDoList(title, toDoList)




    
