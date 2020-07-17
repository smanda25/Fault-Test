#OVERVIEW
#this module contains the functions allowing to manage faults in the circuit
#1]faultyRead
#2]inputGen

#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------


#GOAL= add to the circuit dictionary a faulty dictionary 
#In= circuit, faulty signal
#Out= circuit with a new key => "GatesFaulty":Dic_GateFaulty  
#
#FORMAT OF DIC_GATEFAULY
# "gateFaulty"= "outputFaulty" =[ inFaulty, faultyValue ]

# ** if no faulty, the output will be void

def faultyRead(circuit,faultySignal ):
    
    #initialization of the faulty dictionary
    Dic_GateFaulty={}
    
    #if i receive a faulty Signal
    if faultySignal:
        
        #let's extract the name of the faulty signal
        # fault format= X-SA-1/0    OR     Y-IN-X-SA-1/0
        
        faultySignal=faultySignal.split("-")
        faultyValue=faultySignal[-1]
        
        if faultySignal[1] != "SA":
            #If Y-IN-X-SA-1/0 
            ##########  -->  i've only one gate faulty --> the one( Y ) with the faulty signal( X ) as input 
            
            #let's add it to the faulyList
            gateFaulty="wire_"+faultySignal[0]
            inFaulty="wire_"+faultySignal[2] 
            Dic_GateFaulty[gateFaulty]=[ inFaulty, faultyValue ]
            
        
        else : 
            
            #if X-SA-1/0 i've more faulty gates( all the ones with X as input ) or the fault is at one OUTPUT of the whole circuit
            
            inFaulty="wire_"+faultySignal[0]
            
            #if it is one of the output 
            if inFaulty in circuit["OUTPUTS"][1]:
                    Dic_GateFaulty[inFaulty]=[ "OUTPUT", faultyValue ]
            
            
            #if it is an input of some gates
            for gate in circuit:
                
                #let's find which gates have the faulty signal as input 
                #
                #let's check wich list of the circuit dictionary is a gate 
                #---> the list of a gate in circuit is : [ LOGIC, list of inputs, F/T, value ]
                if (circuit[gate][0] != "INPUT" ) and (len(circuit[gate])==4):
                    
                    #let's check if the gate has ad input the faulty signal 
                    if inFaulty in circuit[gate][1]:
                        #it the gate has as input the faulty signal --> it's faulty
                        Dic_GateFaulty[gate]=[ inFaulty, faultyValue ]
    
        #print(Dic_GateFaulty)
    
    circuit["GatesFaulty"]=Dic_GateFaulty
    return circuit    


#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------
#Goal= generate a list with all the output of a given gate, taking into account of the faults
#IN= circuit dictionary and gateUT
#output= list of the input


def inputGen(circuit, gate):
    
    inputValue=[]
    
    #cicle in the input of the gate
    for inputS in circuit[gate][1] :
        
        #if the gate is faulty i've to check which input is faulty
        if gate in circuit["GatesFaulty"]:
            
            inFaultyName= circuit["GatesFaulty"][gate][0]
            inFaultyValue= circuit["GatesFaulty"][gate][1]
            
            #if inputS is faulty, I assign to it in the inputList the faulty value and not the one presented in the circuit dictionary
            if inputS == inFaultyName :
                inputValue.append(inFaultyValue)
                continue

                
        
        #if the inputS is not faulty or the gate is not faulty, i assign to the signal the value presented the circuit dic
        inputValue.append( circuit[inputS][3] )
            
    
    return inputValue
                

    
    
    
    
    
    
