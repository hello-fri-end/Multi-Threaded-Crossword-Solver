import sys

from crossword import *
from copy import *
from thread import Threads


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def unary_constraint_variable(self,variable, word):
        """
        Does the word satisfy the variable's unary constrains?
        """
        if len(word)!= variable.length:
            self.domains[variable].remove(word)


    def enforce_node_consistency(self):
        #update the dictionary of variable-domains
        # such that for any word in the domain,
        # if word.length> variable.length,
        #remove it
        threads= []

        for var in self.domains:
            for word in self.crossword.words:
                threads.append(Threads(target= self.unary_constraint_variable, args=(var, word)))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()


    def is_positive_overlap(self,X_word, Y_word, X_index, Y_index):
        """
        positive overlap means X_word[X_index] = Y_word[Y_index]
        """
        if(X_word[X_index]== Y_word[Y_index]):
            return True
        else:
            return False

    def is_word_consistent(self,X_word, y, X_index, Y_index):
        """
        will be called by revise function to check for two operlapping varibles wheter a word 
        in X's domain satisfies X's binary constraints i.e if X is assigned word, does that leave any 
        option for Y. If not, remove the word from X's domain
        """
        threads=[]
        for Y_word in self.domains[y]:
            threads.append(Threads(target= self.is_positive_overlap, args= (X_word, Y_word, X_index, Y_index)))

        for thread in threads:
            thread.start()

        for thread in threads:
            if(thread.join()== True):
                return True

        return False



    def revise(self, x, y):
        revised = False
        remove= []
        #if they don't have any common block, there is nothing to revise
        if self.crossword.overlaps[x,y]==None:
            return revised
        else:
            intersection = self.crossword.overlaps[x,y]
            X_index= intersection[0]
            Y_index= intersection[1]
            #loops over all the words in the domain of X
            #for each word check if the letter at X_index doesn't match
            #the letter at Y_index for 0some word in Y's domain
            threads=[]
            for X_word in self.domains[x]:
                threads.append(Threads(target= self.is_word_consistent, args=(X_word,y, X_index, Y_index)))

            for thread in threads:
                thread.start()

            for thread in threads:
                if(thread.join()== False):
                    self.domains[x].remove(thread.args()[0])
                    revised= True

        return revised

    def initial_arcs(self):
        threads=[]
        arcs=[]
        for var1 in self.crossword.variables:
            for var2 in self.crossword.variables:
                if var1==var2:
                    continue
                else:
                    if self.crossword.overlaps[var1,var2]== None:
                        continue
                    else:
                        arcs.append((var1,var2))

        return arcs


    def ac3(self, arcs=None):
        #if arcs is empty , use intial list of arcs
        if arcs==None:
            arcs= self.initial_arcs()
        
        #rest of the logic is same for both cases
        #while stack is non empty

        while (len(arcs))!=0:
            threads=[]
            arc= arcs.pop()
            X= arc[0]
            Y= arc[1]
            if self.revise(X,Y):
                #check if revise emptied the domain of X
                if len(self.domains[X])==0:
                    return False
                #check if current revision affected any other neighbours of X
                for neighbour in self.crossword.neighbors(X):
                    if neighbour==Y:
                        continue
                    else:
                        threads.append(Threads(target= self.revise , args=(neighbour,X)))

                for thread in threads:
                    thread.start()
                        

                for thread in threads:
                    if(thread.join()):
                        if(len(self.domains[thread.args()[0]]) == 0):
                            printf("fcyou")
                            return False

        return True


    def assignment_complete(self, assignment):
        return (len(assignment)== len(self.crossword.variables))


    def no_of_constraints(self,value,assignment, var):
        """
        how many constrains does var= value put on it's neighbours
        """
        count=0
        for neighbour in self.crossword.neighbors(var):
            if neighbour in assignment:
                continue
            else:
                if value in self.domains[neighbour]:
                    count +=1
        return count


    def order_domain_values(self, var, assignment):
        """
        orders the domain of the variable var in increasing order of the no. of contraints it puts on it's neighbours
        """
        number_constrained= dict()
        threads= []

        for value in self.domains[var]:
           threads.append(Threads(target=self.no_of_constraints, args=(value,assignment, var)))

        for thread in threads:
            thread.start()

        for thread in threads:
            number_constrained[thread.args()[0]] = thread.join()

         #sort the dictionary in ascending order
        number_constrained= sorted(number_constrained,key=number_constrained.get)
        return number_constrained


    def values_left_in_domain(self,var):
        """
        no. of values left in the domain of var
        We will also return the degree of var
        """
        return (len(self.domains[var]),len(self.crossword.neighbors(var)))

    def select_unassigned_variable(self, assignment):
        """
        we should choose a variable that has least possible values left in it's domain
        """
        result_var=None
        result_value= (100,100)#large initlization
        threads=[]
        for var in self.crossword.variables:
            if var in assignment:
                continue
            else:
                threads.append(Threads(target= self.values_left_in_domain , args=(var,)))

        for thread in threads:
            thread.start()

        for thread in threads:
            return_value= thread.join()
            if return_value<result_value:
                result_value= return_value
                result_var= thread.args()[0]
        #sort-> first by domain_count and then by degree_count
        return result_var

    def is_consistent(self,assignment, var, value):
        """
        check if assignemnt var= value is consistent with the assignment we've done so far
        """

        for neighbor in self.crossword.neighbors(var):
            if neighbor in assignment:
                if assignment[neighbor] == value:
                    return False

        return True

    def backtrack(self, assignment):
        #if all the variables are assigned values, return assignment
        if self.assignment_complete(assignment):
            return assignment
        var= self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var,assignment):
            if self.is_consistent(assignment, var, value):
                assignment[var]= value
                #make inferences from the new assignment
                arcs= [(neighbour,var) for neighbour in self.crossword.neighbors(var)
                       if neighbour not in assignment
                     ]
                #make a copy of domains before calling ac3 so that
                #changes to domains can be reverted if needed
                t1= Threads(target= deepcopy, args= (self.domains,))
                t1.start()
                if self.ac3(arcs=arcs):
                    result= self.backtrack(assignment)
                    if result!= None:
                        return result
                assignment[var].remove(value)
                self.domains= t1.join()
        return None

                 






def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
