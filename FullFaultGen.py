from __future__ import print_function
import os


#--------------------FUNCTION
#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------


#GOAL= generate the list of the faults
#In= circuit name
#Out= fault list  

#type of bench file's row : INPUT(1)
#1] INPUT     (signal)
#2] OUTPUT    (signal )
#3] LogicName (input1, input2,...)

#type of fault signal
# 1] X-SA-1/0
# 2] Y-IN-X-SA-1/0


def faultGen(bench):
    
    #let's open the bench file
    benchFile = open(bench,"r")
    
    print("----------------"*10)
    print("----------------"*10)
    print("-------"*10+"Fault generation begin"+"--------"*10)


    faults = []
    
    for line in benchFile:
        
        #placeholders for -SA-0 and -SA-1 signal
        stuckAtZero = ""       
        stuckAtOne = ""       
         
        #let's neglet void line
        if (line == "\n"):
            continue
        line = line.replace(" ","")
        line = line.replace("\n","")
        
        #for neglet the comment lines
        if (line[0] == "#"):
            continue
        
        #--------------------------------------------for read an input signal
        #
        if (line[0:5] == "INPUT"):

            #take the name of the signal input signal
            line = line.replace("INPUT","")
            line = line.replace("(","")
            line = line.replace(")","")

            
            #append to the list the faults relative to the input signal
            #
            stuckAtZero = line + "-SA-0"
            stuckAtOne = line + "-SA-1"
            faults.append(stuckAtZero)
            faults.append(stuckAtOne)
            
            #print a feedback to the user
            #
            print("\n\n***\n******" +line + " faults processed" + "******\n")
            print("Current Faults List:")
            print(faults)
            print("\n")
            continue
        
        #----------------------------------------------for read an output signal
        #
        if (line[0:5] == "OUTPUT"):
            #Skip because OUTPUT is written as a " " =  gate() statement later
            continue

        
        #----------------------For read a gate --> "=" means that there is a gate
        #
        if "=" in line:
            
            #division of the line in two piece: output and Input+Logic
            outputName=( line.split('=') )[0]
            InputAndLogic= ( line.split('=') )[1]

            #fault for the output


            #faults for output to put into fault list
            stuckAtZero=outputName+"-SA-0"
            stuckAtOne=outputName+"-SA-1"

            faults.append(stuckAtZero)
            faults.append(stuckAtOne)

            #printing output that faults are generated for
            print("***\n******" +outputName+" faults processed" + "\n\n\n")

            print("Current Faults List:")
            print(faults)
            print("\n")


            Input=( InputAndLogic.split('(') )[1]
            Input=( Input.split(')') )[0]
            Input=Input.split(',') 


            for signal in Input:

                #gate input faults generation
                stuckAtZero=""
                stuckAtOne=""

                
                stuckAtZero=outputName+"-IN-"+signal+"-SA-0"
                stuckAtOne=outputName+"-IN-"+signal+"-SA-1"

                faults.append(stuckAtZero)
                faults.append(stuckAtOne)

                print("******" +outputName+"'s Input: " + signal + " fault processed"+"\n\n\n")
                print(faults)

            continue






        continue
    return faults

#-----------------------------------------------------------------------------------------------------------------------------------
#---- MAIN


def mainFullFaultGen(BenchMFile):
     
    #-------------1] let's generate the list
    #
    faultList = faultGen(BenchMFile)
    print("\n ------------------------Finished generation of Fault list------------------------\n")
    print("Total Fault List: ")
    print (faultList)
    
    
    #--------------2]let's write the list in a file
    #
    
    fflFile=input("\n\n name of the Output file for FullFault list[ press enter for using \'full_f_list.txt\' ]= ")
    
    if not fflFile:
        fflFile="full_f_list.txt"

    outputFile = open(fflFile,"w+")
    
    
    #writing the fault list into full.f.list.txt file
    outputFile.write("# "+BenchMFile +"\n")
    outputFile.write("# full SSA fault list\n")
    outputFile.write("\n")
    
    for fault in faultList:
        #writing the faults one at a time
        outputFile.write(fault)
        outputFile.write("\n")
    #converting int variable n to str stringn so we can write into file
    outputFile.write("\n")
    n=len(faultList)
    stringn=str(n)
    outputFile.write("# total faults: ")
    outputFile.write(stringn)
    outputFile.close
    
    print("--------****-----"*20+"\n")
    
    return fflFile


#If this module is executed alone
if __name__ == "__main__":

    #let's read the name of bench file
    fileName=""
    script_dir = os.path.dirname(__file__)
    while True:  
        print("\n Read benchmark file: use  circuit.bench ? Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            fileName= "circuit.bench"
            break
        else:
            fileName = os.path.join(script_dir, userInput)
            
            if not os.path.isfile(fileName):
                print("File does not exist. \n")
            else:
                fileName= userInput
                break
                
    mainFullFaultGen(fileName)

