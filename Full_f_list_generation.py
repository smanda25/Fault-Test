from __future__ import print_function

import os





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



    # print("\n bookkeeping items in circuit: \n")

    # print(circuit["INPUT_WIDTH"])

    # print(circuit["INPUTS"])

    # print(circuit["OUTPUTS"])

    # print(circuit["GATES"])



    return circuit





# -------------------------------------------------------------------------------------------------------------------- #

# FUNCTION: Main Function

def main():

    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in



    print("Fault List Generator:")



    # Select circuit benchmark file, default is circuit.bench

    while True:

        cktFile = "circuit.bench"

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

    printCkt(circuit)



    # keep an initial (unassigned any value) copy of the circuit for an easy reset

    newCircuit = circuit



    # Select output file, default is output.txt

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





if __name__ == "__main__":

    main()
