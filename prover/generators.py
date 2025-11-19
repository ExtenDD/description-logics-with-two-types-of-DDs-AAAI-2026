#1. World names generator -------------

"""
The three functions below, combined, generate new world names, making sure that the new name has not been used so far
"""

#generator
def world_names():
    """ a generator of world names of the form w1, w2, w3,... """
    a = 'w'
    n = 1
    while True:
        yield a + str(n) 
        n += 1 


# Function that uses the generator
def get_next_world_name(world_names):
    return next(world_names)



def new_world_name(interpretation):
    """ outputs a new world name, checking if it has not been used so far"""
    worlds_counter = world_names()
    
    x = get_next_world_name(worlds_counter)
    while True:
        if x in interpretation._world_names_str:
            x = get_next_world_name(worlds_counter)
        else:
            break
    
    interpretation._world_names_str.update({x})
    return(x)




#2. Fresh atoms generator -------------

"""
The three functions below, combined, generate new atom names, making sure that the new name has not been used so far
"""



#generator
def fresh_atom_names():
    """ a generator of atom names of the form Fresh_Atom_1, Fresh_Atom_2, Fresh_Atom_3,... """
    a = 'Fresh_Atom_'
    n = 1
    while True:
        yield a + str(n)
        n += 1 


# Function that uses the generator
def get_next_fresh_atom(fresh_atom_names):
    return next(fresh_atom_names)



def new_fresh_atom(interpretation):
    """ outputs a new atom name, checking if it has not been used so far"""
    fresh_atoms_counter = fresh_atom_names()
    
    x = get_next_fresh_atom(fresh_atoms_counter)

    while True:
        if x in interpretation._all_atoms_in_interpretation:
            x = get_next_fresh_atom(fresh_atoms_counter)
        else:
            break
    
    interpretation._all_atoms_in_interpretation.update({x})
    return(x)
        

