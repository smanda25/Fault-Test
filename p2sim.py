from __future__ import print_function
import os
import math
import csv
import FullFaultGen
import faultyFunction
import copy



#####-----FORMAT OF CIRCUIT DICTIONARY
# There are 7 types of key-->list/dict
# [ 7 conventional and one for the faults ]
#
# wire_sinaglName : [ "INPUT" , wire_sinaglName, True/False, value]
# wire_sinaglName : [ LOGICAL , INPUT LIST, True/False, value]
# "INPUT_WIDTH    : ['input width:', VALUE]
# "INPUT"         : [ LIST OF INPUT ]
# "OUTPUT"        : [ LIST OF OUTPUT ]
# "GATES"         : [ LIST OF GATES ]
# "GatesFaulty"   : { gateFaulty= [ signalFaulty, valueOfFAULTY ] }
##For part 1
##5 testGen function generate individual test vector files
##For part 2
##We used Vraj's project 1 files to run the simulation



# -----------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------
# Function List:
# 1. netRead: read the benchmark file and build circuit netlist
# 2. gateCalc: function that will work on the logic of each gate, taking into account about faults
# 3. inputRead: function that will update the circuit dictionary made in netRead to hold the line values
# 4. basic_sim: the actual simulation.



# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Reading in the Circuit gate-level netlist file:
def netRead(netName):
    # Opening the netlist file:
    netFile = open(netName, "r")

    # temporary variables
    inputs = []  # array of the input wires
    outputs = []  # array of the output wires
    gates = []  # array of the gate list
    inputBits = 0  # the number of inputs needed in this given circuit

    # main variable to hold the circuit netlist, this is a dictionary in Python, where:
    # key = wire name; value = a list of attributes of the wire
    circuit = {}

    # Reading in the netlist file line by line
    for line in netFile:

        # NOT Reading any empty lines
        if (line == "\n"):
            continue

        # Removing spaces and newlines
        line = line.replace(" ", "")
        line = line.replace("\n", "")

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
            # print(line)
            # print(circuit[line])
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
        lineSpliced = line.split("=")  # splicing the line at the equals sign to get the gate output wire
        gateOut = "wire_" + lineSpliced[0]

        # Error detection: line being made already exists
        if gateOut in circuit:
            msg = "NETLIST ERROR: GATE OUTPUT LINE \"" + gateOut + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
            print(msg + "\n")
            return msg

        # Appending the dest name to the gate list
        gates.append(gateOut)

        lineSpliced = lineSpliced[1].split("(")  # splicing the line again at the "("  to get the gate logic
        logic = lineSpliced[0].upper()

        lineSpliced[1] = lineSpliced[1].replace(")", "")
        terms = lineSpliced[1].split(",")  # Splicing the the line again at each comma to the get the gate terminals
        # Turning each term into an integer before putting it into the circuit dictionary
        terms = ["wire_" + x for x in terms]

        # add the gate output wire to the circuit dictionary with the dest as the key
        circuit[gateOut] = [logic, terms, False, 'U']
        # print(gateOut)
        # print(circuit[gateOut])

    # now after each wire is built into the circuit dictionary,
    # add a few more non-wire items: input width, input array, output array, gate list
    # for convenience

    circuit["INPUT_WIDTH"] = ["input width:", inputBits]
    circuit["INPUTS"] = ["Input list", inputs]
    circuit["OUTPUTS"] = ["Output list", outputs]
    circuit["GATES"] = ["Gate list", gates]

    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: calculates the output value for each logic gate, taking into account about faults
def gateCalc(circuit, node):
    # ----------------------
    # If the output of the gate received ( node ) is a faulty OUTPUT of the whole circuit, it's Needless perform the logical operations --> the outputs of the circuit is stuck
    #
    if node in circuit["GatesFaulty"]:
        if circuit["GatesFaulty"][node][0] == "OUTPUT":
            circuit[node][3] = circuit["GatesFaulty"][node][1]
            return circuit

    # -------------------------
    # inputValue will contain all the input values of this logic gate (node), taking into account about faults
    #
    inputValue = faultyFunction.inputGen(circuit, node)
    #

    # --------- --------- --------- logical operations --------- ---------
    #
    # If the node is an Inverter gate output, solve and return the output
    if circuit[node][0] == "NOT":
        if inputValue[0] == '0':
            circuit[node][3] = '1'
        elif inputValue[0] == '1':
            circuit[node][3] = '0'
        elif inputValue[0] == "U":
            circuit[node][3] = "U"

        else:  # Should not be able to come here
            return -1
        return circuit

    # If the node is a BUFFER gate output, solve and return the output
    if circuit[node][0] == "BUFF":
        if inputValue[0] == '0':
            circuit[node][3] = '0'
        elif inputValue[0] == '1':
            circuit[node][3] = '1'
        elif inputValue[0] == "U":
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

        for inS in inputValue:
            if inS == '0':
                circuit[node][3] = '0'
                break
            if inS == "U":
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

        for inS in inputValue:
            if inS == '0':
                circuit[node][3] = '1'
                break
            if inS == "U":
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

        for inS in inputValue:
            if inS == '1':
                circuit[node][3] = '1'
                break
            if inS == "U":
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

        for inS in inputValue:
            if inS == '1':
                circuit[node][3] = '0'
                break
            if inS == "U":
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

        for inS in inputValue:
            if inS == '1':
                count += 1  # For each 1 bit, add one count
            if inS == "U":
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
        # *for term in terminals:
        for inS in inputValue:
            if inS == '1':
                count += 1  # For each 1 bit, add one count
            if inS == "U":
                circuit[node][3] = "U"
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        return circuit

    # Error detection... should not be able to get at this point
    return circuit[node][0]


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Updating the circuit dictionary with the input line, and also resetting the gates and output lines
def inputRead(circuit, line):
    # Checking if input bits are enough for the circuit
    if len(line) < circuit["INPUT_WIDTH"][1]:
        return -1

    # Getting the proper number of bits:
    line = line[(len(line) - circuit["INPUT_WIDTH"][1]):(len(line))]

    # Adding the inputs to the dictionary
    # Since the for loop will start at the most significant bit, we start at input width N
    i = circuit["INPUT_WIDTH"][1] - 1
    inputs = list(circuit["INPUTS"][1])
    # dictionary item: [(bool) If accessed, (int) the value of each line, (int) layer number, (str) origin of U value]
    for bitVal in line:
        bitVal = bitVal.upper()  # in the case user input lower-case u
        circuit[inputs[i]][3] = bitVal  # put the bit value as the line value
        circuit[inputs[i]][2] = True  # and make it so that this line is accessed

        # In case the input has an invalid character (i.e. not "0", "1" or "U"), return an error flag
        if bitVal != "0" and bitVal != "1" and bitVal != "U":
            return -2
        i -= 1  # continuing the increments

    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: the actual simulation #
def basic_sim(circuit):
    # QUEUE and DEQUEUE
    # Creating a queue, using a list, containing all of the gates in the circuit
    queue = list(circuit["GATES"][1])
    i = 1

    # choiceS=input("do you want a step by step simulation? [yes/no] -->")
    choiceS = "no"

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
        for term in circuit[curr][1]:
            if not circuit[term][2]:
                term_has_value = False
                break

        if term_has_value:
            circuit[curr][2] = True
            circuit = gateCalc(circuit, curr)

            # ERROR Detection if LOGIC does not exist
            if isinstance(circuit, str):
                print(circuit)
                return circuit

            if choiceS == "yes":
                print("Progress: updating " + curr + " = " + circuit[curr][3] + " as the output of " + circuit[curr][
                    0] + " for:")
                for term in circuit[curr][1]:
                    print(term + " = " + circuit[term][3])
                print("\nPress Enter to Continue...")
                input()


        else:
            # If the terminals have not been accessed yet, append the current node at the end of the queue
            queue.append(curr)

    return circuit



def intTobinary_add(tempInput):
    add = int(tempInput,2) + 1
    return bin(add)

def testGenA(s0, numInputs,outputFile):

    
    F = open(outputFile,'a')
    F.truncate(0)
    TV_A=[]
    temp = bin(int(s0))
    TV_A.append(temp)
    str_temp = str(TV_A[0][2:].zfill(numInputs))
    F.write(str(TV_A[0][2:].zfill(numInputs)[(len(str_temp)-numInputs):])+'\n')
    for i in range(1,255):
        if(temp==bin(pow(2,int(numInputs)-1))):
            temp=bin(0)
        else:
            temp = intTobinary_add(TV_A[i-1])
        TV_A.append(temp)
        str_temp = str(TV_A[i][2:].zfill(numInputs))
        F.write(str_temp[(len(str_temp)-numInputs):]+'\n')
    F.close()
    return
def testGenB(s0, numInputs, outputFile):
    block = math.ceil(numInputs/8);
    F = open(outputFile,'a')
    F.truncate(0)
    pattern = ''
    TV_B=[]

    temp = bin(int(s0))

    for i in range(255):
        pattern = ''

        for j in range(block):
            pattern = temp[2:].zfill(8) + pattern
           
        if(temp=='0b11111111'):
            put='0b00000000'
        else:
            put = intTobinary_add(temp)
        temp=put
        TV_B.append(pattern[(len(pattern)-numInputs):])
        F.write(TV_B[i] + '\n')
    F.close()

    
 #Test vector C generation
def testGenC(s0,numInputs, outputFile):
    block = math.ceil(numInputs/8);
    F = open(outputFile,'a')
    F.truncate(0)
    pattern = ''
    TV_C=[]
    temp = bin(int(s0))

    nextTVStart = temp
    for i in range(255):
        pattern = ''
        ##updating temp to previous s1
        temp = nextTVStart
        for j in range(block):
            pattern = temp[2:].zfill(8) + pattern
            if(int(temp,2)==255):
                temp = bin(0)
            else:
                temp = intTobinary_add(temp)
            ##implementing s[i+1] for next test vector
            if j == 0:
                nextTVStart = temp

        TV_C.append(pattern[(len(pattern)-numInputs):])
        F.write(TV_C[i] + '\n')
    F.close()

def LFSR(index_Val, last_val):
    index_Val = int(index_Val) ^ int(last_val)
    return index_Val
def testGenD(s0,numInputs, outputFile):

    temp=bin(int(s0))[2:].zfill(8)
    F = open(outputFile,'a')
    block = math.ceil(numInputs/8);
    F.truncate(0)
    pattern = ''
    TV_D=[]

    for i in range(255):
        pattern =''
        for x in range(block):
            pattern = temp + pattern
        TV_D.append(pattern[(len(pattern) - numInputs):])
        F.write(TV_D[i] + '\n')
        temp = list(temp[len(temp)::-1])
        temp_other = temp[:]
        for index in range(8):
            if(index == 2 or index == 3 or index == 4):
                temp_other[index]=temp[index-1]
                temp_other[index]=LFSR(temp_other[index], temp[7])

            elif( index == 0):
                temp_other[index] = temp[7]

            else:
                temp_other[index]=temp[index-1]


        temp = ''.join(str(x) for x in temp_other[len(temp)::-1])





    F.close()


#for TV_E generation
def testGenE(s0,numInputs, outputFile):

    exact_s0=(bin(int(s0)))[2:]
    eightbit_s0=exact_s0.zfill(8)
    reverses0=eightbit_s0[::-1]
    revs0_dummy=reverses0
    F = open(outputFile,'a')
    block = math.ceil(int(numInputs)/8)
    F.truncate(0)
    TV_E=[]
    for j in range(0,255):


        if(j!=0):
            reverses0=revs0_dummy
        for i in range(0,block):
            if(i==0):
                result=revs0_dummy

            lastbit=reverses0[7]
            b=[]
            if(lastbit=='0'):
                b=lastbit+reverses0[0]+reverses0[1:7]
            else:
                b=lastbit+reverses0[0]
                if(reverses0[1]=='0'):
                    b=b+'1'
                else:
                    b=b+'0'

                if(reverses0[2]=='0'):
                    b=b+'1'
                else:
                    b=b+'0'

                if(reverses0[3]=='0'):
                    b=b+'1'
                else:
                    b=b+'0'
                b=b+reverses0[4:7]
            pattern=""
            pattern=pattern+b
            if(i==0):
                revs0_dummy=b
            result=result+pattern
            reverses0=b

        TV_E.append((result[0:int(numInputs)])[::-1])
        F.write(TV_E[j] +'\n')
    F.close()











def main():
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    userInput = 'c432.bench'
    print("TV Generation\n")
    while True:
        cktFile = "c432.bench"
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
    print("\n Finished processing benchmark file and built netlist dictionary: \n")
    
    print("Enter a initial seed for test vector generation:")
    init_seed = input()
    print("Choose what you'd like to do (1,2)\n"
          "1: Test Vector Generation\n2: Fault Coverage Simulation\n")
    num = input()
    # keep an initial (unassigned any value) copy of the circuit for an easy reset
    newCircuit = circuit

    numInput = circuit['INPUT_WIDTH'][1]
    tv1_out = 'TV_A.txt'
    tv2_out = 'TV_B.txt'
    tv3_out = 'TV_C.txt'
    tv4_out = 'TV_D.txt'
    tv5_out = 'TV_E.txt'
    TV_A = []
    TV_B = []
    TV_C = []
    TV_D = []
    TV_E = []
    filename = [tv1_out,tv2_out,tv3_out,tv4_out,tv5_out]
    percent_A = []
    percent_B = []
    percent_C = []
    percent_D = []
    percent_E = []
    temp = 'A'
    temp = bytes(temp, 'utf-8')
    
    tv_data = []

    if(int(num)==1):

        testGenA(init_seed,numInput, tv1_out)
        testGenB(init_seed,numInput,tv2_out)
        testGenC(init_seed,numInput,tv3_out)
        testGenD(init_seed, numInput, tv4_out)
        testGenE(init_seed, numInput, tv5_out)
    elif(int(num)==2):

        print("Enter a batch size [1,10] for generating csv file")
        batchSize = input()
        faultFile= 'f_list.txt'


        while True:
            print("Enter name to read in fault list: 'ENTER' to run full fault list or type filename")
            userInput = input()
            if userInput == "":
                Faultlist =   FullFaultGen.faultGen(cktFile)

                with open(faultFile, 'w') as filehandle:  # Writing the faults from circuit benchmark file.
                    for line in Faultlist:
                        filehandle.write("%s\n" % line)
                    filehandle.close()
                break
            else:
                faultFile = os.path.join(script_dir, userInput)
                if not os.path.isfile(faultFile):
                    print("File does not exist. \n")
                else:
                    break

        for file in filename:
            with open(file,'r') as tvFile:
                for line in tvFile:
                    if(file == 'TV_A.txt'):
                        TV_A.append(line.replace('\n',''))
                    elif file == 'TV_B.txt':
                        TV_B.append(line.replace('\n',''))
                    elif file == 'TV_C.txt':
                        TV_C.append(line.replace('\n',''))
                    elif file == 'TV_D.txt':
                        TV_D.append(line.replace('\n',''))
                    elif file == 'TV_E.txt':
                        TV_E.append(line.replace('\n',''))

            tvFile.close()

        tv_data.append(TV_A)
        tv_data.append(TV_B)
        tv_data.append(TV_C)
        tv_data.append(TV_D)
        tv_data.append(TV_E)
        FAULTs=[]
        inFault = open(faultFile, 'r')
        for line in inFault:
            # if the line is not void
            if len(line) > 1:
                # if the line is not a comment
                if line[0] != "#":
                    f = (line.split()[0])

                    # let's check if the Faults is correct
                    # fault format= X-SA-1/0 or Y-IN-X-SA-1/0
                    #
                    ff = line.split("-")
                    if (ff[1] != "SA") and (ff[1] != "IN"):
                        print("ERROR: the faults{0} is not valid".format(f))
                        exit()

                    else:
                        FAULTs.append(f)
        inFault.close()
        i = 0
        max_tv = int(batchSize)*25
        for tv in tv_data:
            print('Simulating Test Vector for TV: '+ str(temp))
            temp = bytes([temp[0]+1])

            detected=[]
            batch = 0
            i = i + 1
            undFault = FAULTs.copy()
            for tv_num in range(len(tv)):
                batch = batch + 1
                circuit = copy.deepcopy(newCircuit)
                if tv_num==max_tv:
                    break

                print("\n ** ----------------  Circuit Simulation for tv= {0} -------- -------- ** ".format(tv[tv_num]))
                circuit = inputRead(circuit,tv[tv_num])
                circuit = faultyFunction.faultyRead(circuit, "")
                circuit = basic_sim(circuit)

                # check if the simulatore gives an error
                # errors: "falseFS" for an error in the fault signal
                #         "falseTV" for an error in the tv
                #         "falseOUT" for an error in the output
                output = ""
                for y in circuit["OUTPUTS"][1]:
                    if not circuit[y][2]:
                        output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                        return "falseOUT"
                    output = str(circuit[y][3]) + output
                good_sim = output

                badOut = []
                for f in FAULTs:
                   ## print("Simulating Fault "+f +'\n')



                    bad_output =''
                    circuit = copy.deepcopy(newCircuit)
                    circuit = faultyFunction.faultyRead(circuit, f)
                    circuit = inputRead(circuit, tv[tv_num])
                    if f:
                        typeOfCircuit = " FAULT= [ {0} ]  Input={1}".format(f, tv)
                    else:
                        typeOfCircuit = " Input ={0}\n".format(tv)

                        # print("\n *** Simulating the circuit with " + typeOfCircuit )


                    circuit = basic_sim(circuit)

                    # ----------------------
                    # If the faulty signal is both an input and an output, it will not be scanned by the gatecalculator
                    #
                    if f:
                        for fau in circuit["GatesFaulty"]:
                            if fau in circuit["OUTPUTS"][1]:
                                if not (fau in circuit["GATES"][1]):
                                    circuit[fau][3] = circuit["GatesFaulty"][fau][1]
                    for y in circuit["OUTPUTS"][1]:
                        if not circuit[y][2]:
                            output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                            return "falseOUT"
                        bad_output = str(circuit[y][3]) + bad_output
                    badOut.append(bad_output)

                for (f, badO) in zip(FAULTs, badOut):
                    # detected if badOutput == goodOutput
                    if badO != good_sim:
                        # if detected
                        # 1] fault&badOutput added to the detected list
                        # 2] fault removed from the undetected faults <-> it is not yet removed
                        detected.append(f)
                        if f in undFault:
                            undFault.remove(f)
                num_detect = len(FAULTs)-len(undFault)
                if batch == int(batchSize):
                    batch = 0
                    percentage = num_detect/len(FAULTs)
                    if i == 1:
                        percent_A.append('{:.1%}'.format(percentage))
                    elif i == 2:
                        percent_B.append('{:.1%}'.format(percentage))
                    elif i == 3:
                        percent_C.append('{:.1%}'.format(percentage))
                    elif i == 4:
                        percent_D.append('{:.1%}'.format(percentage))
                    elif i == 5:
                        percent_E.append('{:.1%}'.format(percentage))

        initLine = ['batch#', 'A', 'B', 'C', 'D', 'E', 'seed = ' + bin(int(init_seed))[2:].zfill(8), 'batch size: ' + batchSize]
        csvFile = open('f_cvg.csv','a')
        csvFile.truncate(0)
        wr = csv.writer(csvFile,delimiter =',')
        wr.writerow(initLine)
        for i in range(25):
            wr.writerow([str(i+1),str(percent_A[i]),str(percent_B[i]),str(percent_C[i]),str(percent_D[i]),str(percent_E[i]),'',''])












if __name__ == "__main__":
        main()
