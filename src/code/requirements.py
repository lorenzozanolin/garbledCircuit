import os.path

def saveSet(set,owner):
    """Save a set into the owners folder.

    Args:
        set: The set, is a list of integers.
        owner: a for Alice, b for Bob.

    Returns:
        None.
    """
    directory = './sets/'
    filename = "alice.txt" if owner == "a" else "bob.txt"
    owner_path = os.path.join(directory, filename)
    if not os.path.isdir(directory):
        os.mkdir(directory)
    
    f = open(owner_path, "w")
    set_values = ' '.join([str(w) for w in set])
    f.write(set_values)
    f.close()

def readSet(owner):
    """Read a set from the owners folder.

    Args:
        owner: a for Alice, b for Bob.

    Returns:
        set: the set as a list of integers.
    """
    directory = './sets/'
    filename = "alice.txt" if owner == "a" else "bob.txt"
    owner_path = os.path.join(directory, filename)
    if not os.path.isdir(directory):
        os.mkdir(directory)
    
    f = open(owner_path,"r")
    set = list(f.readline().split(" "))
    set = [int(x) for x in set]
    f.close()
    return set

def verifyOperation(computedResult):
    """Checks whether the computation has produced a correct result comparing the computed result (by the circuit) with the correct one obtained summing the two sets in the files
    
    Args:
        computedResult: integer representing the computed result by Yao's protocol.

    Returns:
        1 if the computation is correct, 0 otherwise.
    """
    #reads value from original sets, does sum and checks whether is equal to the computed value
    if computedResult == (sum(readSet("a"))+sum(readSet("b"))):  
        return 1
    else:
        return 0

def askForInput(party):
    """Ask for input via console, so user can directly insert the set for party.

    Args:
        party: a for Alice, b for Bob
        
    Raise:
        exception if the sum is higher than 
        
    Returns:
        The set that user inserts.
    """
    user = "Alice" if party == "a" else "Bob"
    numbers = list(map(int, input(f"Enter the list of integers of {user}'s set: ").strip().split(' ')))
    
    if(sum(numbers)>255):
        raise Exception("sum of the numbers is too high, you must enter numbers whose sum is between 0-255")
    
    return numbers