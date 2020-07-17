from __future__ import print_function
import os
import copy
import math

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Neatly prints the Circuit Dictionary:
def printCkt(circuit):
    print("INPUT LIST:")
    for x in circuit["INPUTS"][1]:
        print(x + "= ", end='')
        print(circuit[x])

    print("\nOUTPUT LIST:")
    for x in circuit["OUTPUTS"][1]:
        print(x + "= ", end='')
        print(circuit[x])

    print("\nGATE list:")
    for x in circuit["GATES"][1]:
        print(x + "= ", end='')
        print(circuit[x])
    print()


#---------------------------------------------------------------------------------------------#

# FUNCTION: Reading in the Circuit gate-level netlist file:

d={} #
def netRead(netName):
    # Opening the netlist file:
    netFile = open(netName, "r")


    # temporary variables
    inputs = []     # array of the input wires
    outputs = []    # array of the output wires
    gates = []      # array of the gate list
    inputBits = 0   # the number of inputs needed in this given circuit



    # main variable to hold the circuit netlist, this is a dictionary in Python, where:
    # key = wire name; value = a list of attributes of the wire
    circuit = {}

    # Reading in the netlist file line by line
    for line in netFile:

        # NOT Reading any empty lines
        if (line == "\n"):
            continue

        # Removing spaces and newlines
        line = line.replace(" ","")
        line = line.replace("\n","")

        # NOT Reading any comments
        if (line[0] == "#"):
            continue

        # @ Here it should just be in one of these formats:
        # INPUT(x)
        # OUTPUT(y)
        # z=LOGIC(a,b,c,...)

        # Read a INPUT wire and add to circuit:
        if (line[0:5] == "INPUT"):
            # Removing everything but the line variable name
            line = line.replace("INPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            # Format the variable name to wire_*VAR_NAME*
            line = "wire_" + line

            # Error detection: line being made already exists
            if line in circuit:
                msg = "NETLIST ERROR: INPUT LINE \"" + line + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
                print(msg + "\n")
                return msg

            # Appending to the inputs array and update the inputBits
            inputs.append(line)

            # add this wire as an entry to the circuit dictionary
            circuit[line] = ["INPUT", line, False, 'U']

            inputBits += 1
            print(line)
            print(circuit[line])
            continue


        # Read an OUTPUT wire and add to the output array list
        # Note that the same wire should also appear somewhere else as a GATE output
        if line[0:6] == "OUTPUT":
            # Removing everything but the numbers
            line = line.replace("OUTPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            # Appending to the output array
            outputs.append("wire_" + line)
            continue

        # Read a gate output wire, and add to the circuit dictionary
        lineSpliced = line.split("=") # splicing the line at the equals sign to get the gate output wire
        gateOut = "wire_" + lineSpliced[0]

        # Error detection: line being made already exists
        if gateOut in circuit:
            msg = "NETLIST ERROR: GATE OUTPUT LINE \"" + gateOut + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
            print(msg+"\n")
            return msg

        # Appending the dest name to the gate list
        gates.append(gateOut)

        lineSpliced = lineSpliced[1].split("(") # splicing the line again at the "("  to get the gate logic
        logic = lineSpliced[0].upper()


        lineSpliced[1] = lineSpliced[1].replace(")", "")
        terms = lineSpliced[1].split(",")  # Splicing the the line again at each comma to the get the gate terminals
        # Turning each term into an integer before putting it into the circuit dictionary
        terms = ["wire_" + x for x in terms]

        # add the gate output wire to the circuit dictionary with the dest as the key
        circuit[gateOut] = [logic, terms, False, 'U']
        print(gateOut)
        print(circuit[gateOut])

    # now after each wire is built into the circuit dictionary,
    # add a few more non-wire items: input width, input array, output array, gate list
    # for convenience

    circuit["INPUT_WIDTH"] = ["input width:", inputBits]
    circuit["INPUTS"] = ["Input list", inputs]
    circuit["OUTPUTS"] = ["Output list", outputs]
    circuit["GATES"] = ["Gate list", gates]


    print("\n bookkeeping items in circuit: \n")
    print(circuit["INPUT_WIDTH"])
    print(circuit["INPUTS"])
    print(circuit["OUTPUTS"])
    print(circuit["GATES"])



    return circuit

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: calculates the output value for each logic gate
def gateCalc(circuit, node, cycle):
    global d

    # terminal will contain all the input wires of this logic gate (node)

    terminals = list(circuit[node][1])

    # If the node is a DFF, solve and return the output
    if circuit[node][0] == "DFF":

        if circuit[terminals[0]][3] == '0':
            next_output='0'
        elif circuit[terminals[0]][3] == '1':
            next_output = '1'
        elif circuit[terminals[0]][3] == "U":
            next_output = "U"
        else:  # Should not be able to come here
            return "U"

        if cycle==1:
            circuit[node][3] = "U"
            return circuit
        else:
            p=circuit[node][1] # to get the input of the DFF
            circuit[node][3]=d[p[0]]
            d[p[0]]=next_output

            return circuit

    # If the node is an Inverter gate output, solve and return the output
    if circuit[node][0] == "NOT":
        if circuit[terminals[0]][3] == '0':
            circuit[node][3] = '1'
        elif circuit[terminals[0]][3] == '1':
            circuit[node][3] = '0'
        elif circuit[terminals[0]][3] == "U":
            circuit[node][3] = "U"
        else:  # Should not be able to come here
            return -1
        return circuit

    # If the node is an AND gate output, solve and return the output
    elif circuit[node][0] == "AND":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a flag that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 at any input terminal, AND output is 0. If there is an unknown terminal, mark the flag
        # Otherwise, keep it at 1
        for term in terminals:
            if circuit[term][3] == '0':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        return circuit

    # If the node is a NAND gate output, solve and return the output
    elif circuit[node][0] == "NAND":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 terminal, NAND changes the output to 1. If there is an unknown terminal, it
        # changes to "U" Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '0':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
                break

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        return circuit

    # If the node is an OR gate output, solve and return the output
    elif circuit[node][0] == "OR":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, OR changes the output to 1. Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        return circuit

    # If the node is an NOR gate output, solve and return the output
    if circuit[node][0] == "NOR":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, NOR changes the output to 0. Otherwise, keep it at 1
        for term in terminals:
            print(circuit[term][3],"asd")
            if circuit[term][3] == '1':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        return circuit

    # If the node is an XOR gate output, solve and return the output
    if circuit[node][0] == "XOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there are an odd number of terminals, XOR outputs 1. Otherwise, it should output 0
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        return circuit

    # If the node is an XNOR gate output, solve and return the output
    elif circuit[node][0] == "XNOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there is a single 1 terminal, XNOR outputs 0. Otherwise, it outputs 1
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # odd number of 1 returns 0 for XNOR.
            circuit[node][3] = '0'
        else:  # even number of 1 returns 1 for XNOR
            circuit[node][3] = '1'
        return circuit

    # Error detection... should not be able to get at this point

    return circuit[node][0]

#---------------------------------------------------------------------------------------------------------------------#
def inputRead(circuit, line):
    # Checking if input bits are enough for the circuit
    if len(line) < circuit["INPUT_WIDTH"][1]:
        return -1

    # Getting the proper number of bits:
    line = (line[(len(line) - circuit["INPUT_WIDTH"][1]):(len(line))])

    # Adding the inputs to the dictionary
    # Since the for loop will start at the most significant bit, we start at input width N
    i = circuit["INPUT_WIDTH"][1] - 1
    inputs = list(circuit["INPUTS"][1])
    # dictionary item: [(bool) If accessed, (int) the value of each line, (int) layer number, (str) origin of U value]
    for bitVal in line:
        bitVal = bitVal.upper() # in the case user input lower-case u
        circuit[inputs[i]][3] = bitVal # put the bit value as the line value
        circuit[inputs[i]][2] = True  # and make it so that this line is accessed

        # In case the input has an invalid character (i.e. not "0", "1" or "U"), return an error flag
        if bitVal != "0" and bitVal != "1" and bitVal != "U":
            return -2
        i -= 1 # continuing the increments

    return circuit

#---------------------------------------------------------------------------------------------------------------------#
# FUNCTION: the actual simulation #
def basic_sim(circuit,cycle):
    global d

    # QUEUE and DEQUEUE
    # Creating a queue, using a list, containing all of the gates in the circuit

    queue = list(circuit["GATES"][1])
    i = 1

    while True:
        i -= 1

        # If there's no more things in queue, done
        if len(queue) == 0:
            break

        # Remove the first element of the queue and assign it to a variable for us to use
        curr = queue[0]
        queue.remove(curr)

        # initialize a flag, used to check if every terminal has been accessed
        term_has_value = True

        # Check if the terminals have been accessed
        if circuit[curr][0]=="DFF":
            print("It is DFF")

        else:
            for term in circuit[curr][1]:

                if not circuit[term][2]:
                    term_has_value = False
                    break

        if term_has_value:

            circuit[curr][2] = True
            circuit = gateCalc(circuit, curr,cycle)

            # ERROR Detection if LOGIC does not exist
            if isinstance(circuit, str):
                print(circuit)
                return circuit

            print("Progress: updating " + curr + " = " + str(circuit[curr][3]) + " as the output of " + circuit[curr][0] + " for:")
            for term in circuit[curr][1]:
                print(term + " = " + str(circuit[term][3]))
            # print("\nPress Enter to Continue...")
            # input()

        else:
            # If the terminals have not been accessed yet, append the current node at the end of the queue
            queue.append(curr)

    for term in circuit:
        if circuit[term][0]=="DFF":
            inp=circuit[term][1][0] # inp is input of DFF
            circuit[term][3]=circuit[inp][3]
            d[inp] = circuit[term][3]

    return circuit

#----------------------------------------------------------------------------------------------------------------------#
#

def faultGen(circuit, outputFile):
    counter = 0

    for x in circuit["INPUTS"][1]:

        outputFile.write(x[5:] + "-SA-0" + "\n")
        outputFile.write(x[5:] + "-SA-1" + "\n")
        counter = counter + 2

    for x in circuit["GATES"][1]:

        outputFile.write(x[5:] + "-SA-0" + "\n")
        outputFile.write(x[5:] + "-SA-1" + "\n")
        counter = counter + 2

        for y in circuit[x][1]:

            outputFile.write(x[5:] + "-IN-" + y[5:] + "-SA-0" + "\n")
            outputFile.write(x[5:] + "-IN-" + y[5:] + "-SA-1" + "\n")
            counter = counter + 2

    outputFile.write("\n# total faults: " + str(counter) + "\n")


#----------------------------------------------------------------------------------------------------------------------#
# Main function

def main():
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    print("TV Generation\n")
    while True:
        cktFile = "s27.bench"
        print("\n Read circuit benchmark file: use " + cktFile + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            cktFile = os.path.join(script_dir, userInput)
            if not os.path.isfile(cktFile):
                print("File does not exist. \n")
            else:
                break

    print("\n Reading " + cktFile + " ... \n")
    circuit = netRead(cktFile)

    print("\n Enter the Cycle number n :")
    cycle=input()

    if(cycle==""):
        cycle=5

    print("\n Finished processing benchmark file and built netlist dictionary: \n")

    # keep an initial (unassigned any value) copy of the circuit for an easy reset
    newCircuit = circuit

    # Select input file, default is input.txt
    while True:

        print("\n Enter the test vector : ")
        inputName=input()

        inputsnum=circuit["INPUT_WIDTH"][1] # to get the number of inputs

        inputs=2**inputsnum # to get the number of input combinations for the given set of inputs
        if inputName == "":
            inputName=bin(0)[2:].zfill(inputsnum)
            break

        elif int(inputName)>=0:
            inputName=bin(int(inputName))[2:].zfill(inputsnum)
            break

        elif (int(inputName) < 0):
            num = int(inputName)+inputs #after converting into the negative num into a positive num
            inputName=bin(int(num))[2:].zfill(inputsnum)
            break
        elif (int(inputName)<-inputs and int(inputName)>inputs):
            print("Given Input is out of range")
            break
        else:
            break

    while True:
        print("\n Enter the fault in the circuit:")
        userInput = input()

        if userInput == "":
            f_listName=circuit["INPUTS"][1][0].split("_")[1]+"-SA-0"
            break
        else:
            f_listName=userInput
            break

    # Select output file, default is output.txt
    while True:
        outputName = "fault_sim_result.txt"
        print("\n Write output file: use " + outputName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            outputName = os.path.join(script_dir, userInput)
            break

    # Note: UI code;
    # **************************************************************************************************************** #

    print("\n *** Simulating the" + userInput + " file and will output in" + outputName + "*** \n")

    outputFile = open(outputName, "w")
    output = ""
    outputFile.write("# fault sim result \n# circuit bench: " + cktFile + " \n# fault: " + f_listName + " \n# TV: " + inputName + "\n\n")

    print("\n before processing circuit dictionary...")
    # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
    # printCkt(circuit)
    # print(circuit)
    print("\n ---> Now ready to simulate INPUT = " + inputName)
    # circuit = inputRead(circuit, inputName)
    # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
    printCkt(circuit)
    # print(circuit)

    cycle=int(cycle)
    cycledummy=cycle
    cycledummy1=cycle
    cycledummy2=cycle

    outputmain={}
    while cycle:
        circuit = inputRead(circuit, inputName)

        if circuit == -1:
            print("INPUT ERROR: INSUFFICIENT BITS")
            outputFile.write(" -> INPUT ERROR: INSUFFICIENT BITS" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue
        elif circuit == -2:
            print("INPUT ERROR: INVALID INPUT VALUE/S")
            outputFile.write(" -> INPUT ERROR: INVALID INPUT VALUE/S" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue

        cycledummy3=cycledummy1-cycle+1
        circuit = basic_sim(circuit,cycledummy3)
        cycle=cycle-1

        print("\n *** Finished simulation - resulting circuit: \n")
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        # printCkt(circuit)
        print(circuit)


        for y in circuit["OUTPUTS"][1]:
            if not circuit[y][2]:
                output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                break
            outputmain[cycledummy3]=str(circuit[y][3])
            output = str(circuit[y][3]) + output

        print("\n *** Summary of simulation: ")

        for key in circuit:
            if (key[0:5] == "wire_"):
                circuit[key][2] = False

    outputFile.write("Output value -> " + output + " (good)(Max Cycle to Min cycle)\n")

#------------------------------------------------------------------------------------------------------------------#

    circuit_fault = copy.deepcopy(circuit)
    print(circuit_fault)

    for key in circuit_fault:
        if (key[0:5] == "wire_"):
            circuit_fault[key][2] = False
            circuit_fault[key][3] = 'U'
    print(circuit_fault)

    # After each input line is finished, reset the circuit

    while cycledummy:
        cyc=cycledummy2-cycledummy+1
        if(cyc==1):    # If ruuning for the first time
            f_listNamedummy=f_listName
            circuit_fault = inputRead(circuit_fault, inputName)
            print(f_listName)
            f_listName=f_listName.split("-")
            f_listName[0]="wire_"+f_listName[0]

            if(f_listName[1] == "IN"):
                circuit_fault["faultWire"] = ["FAULT", "NONE", True, f_listName[4]]
                for key in circuit_fault:
                    if(f_listName[0] == key[5:]):
                        Index = 0
                        for Input in circuit_fault[key][1]:
                            if(f_listName[2] == Input[5:]):
                                circuit_fault[key][1][Index] = "faultWire"
                            Index += 1


            elif(f_listName[1] == "SA"):
                for key in circuit_fault:
                    if(f_listName[0] == key):
                       circuit_fault[key][3] = f_listName[2]
                       circuit_fault[key][2] = True

        else:

            circuit_fault = inputRead(circuit_fault, inputName)

            if(f_listName[1] == "IN"):
                circuit_fault["faultWire"] = ["FAULT", "NONE", True, f_listName[4]]
                for key in circuit_fault:
                    if(f_listName[0] == key[5:]):
                        Index = 0
                        for Input in circuit_fault[key][1]:
                            if(f_listName[2] == Input[5:]):
                                circuit_fault[key][1][Index] = "faultWire"
                            Index += 1

            elif(f_listName[1] == "SA"):
                for key in circuit_fault:
                    if(f_listName[0] == key):
                       circuit_fault[key][3] = f_listName[2]
                       circuit_fault[key][2] = True

        print("\n *** Running the Fault Test... \n")

        cycledummy3=cycledummy2-cycledummy+1
        circuit_fault = basic_sim(circuit_fault,cycledummy3)
        cycledummy=cycledummy-1

        output_fault = ""
        output_faultmain={}
        for y in circuit_fault["OUTPUTS"][1]:
            if circuit_fault[y][2] == False:
                output_fault = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                break
            output_faultmain[cycledummy3]=str(circuit_fault[y][3])
            output_fault = str(circuit_fault[y][3]) + output_fault

        outputFile.write("\n")

        # For detection part of fault
        if(outputmain[cycledummy3] != output_faultmain[cycledummy3]):
            if(f_listName[1] == "IN"):
                outputFile.write("Fault Detected in the cycle number: "+str(cycledummy3)+ "\n"+ ": ")
                outputFile.write(f_listNamedummy + " -> " + output_fault + "\n")

            elif(f_listName[1] == "SA"):
                outputFile.write("Fault Detected in the cycle number: "+str(cycledummy3)+ "\n"+ ": ")
                outputFile.write(f_listNamedummy + " -> " + output_fault + "\n")


        print("\n *** Now resetting circuit back to unknowns... \n")
        for key in circuit_fault:
            if (key[0:5]=="wire_"):
                circuit_fault[key][2] = False

        outputFile.write("\n")

    # After each input line is finished, reset the circuit
    print("\n *** Now resetting circuit back to unknowns... \n")

    for key in circuit:
        if (key[0:5]=="wire_"):
            circuit[key][2] = False
            circuit[key][3] = 'U'

    print("\n circuit after resetting: \n")
    # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
    # printCkt(circuit)
    print(circuit)

    print("\n*******************\n")

    while True:
        outputName = "f_list.txt"
        print("\n Write output file: use " + outputName + "?" + " Enter to accept or type filename: ")
        userInput = input()

        if userInput == "":
            break
        else:
            outputName = os.path.join(script_dir, userInput)
            break

    outputFile = open(outputName, "w")
    #printCkt(circuit)
    outputFile.write("# " + cktFile + "\n# full SSA fault list\n\n")

    faultGen(circuit, outputFile)


    outputFile.close
    #exit()


if __name__ == "__main__":
        main()
