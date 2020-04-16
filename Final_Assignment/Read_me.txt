
Run the main file, all the options can be changed through the gui in the root object.

This includes:
	-planform parameters
	-airfoil coordinate files (name of any of the files that is in the airfoils folder)
	-flap type
	-flap deflection

Some notes:
	-I have tested the code with many airfoils and with most it performs fine
	-Some surfaces are wrinkled if there are too few airfoil coordinates, like "ex4" used for flower,
         I need to add some error message to not allow such files.
	-Im not sure how to check if the airfoil has an airfoil shape (to raise an error), obviously if 
	 it does not then the result will not make any sence and code might crash. Also, if the airfoil is
	 not sufficiently smooth (like "ex8"), the interpollation of coordinates will create a wavy surface.
	-Flower flap does not work well with very sharp TEs (such as "ex2" airfoil)
	 for this I added some backup code that splits surfaces in a different way, when this is used, 
	 the flaps turn red (the whole splitting plane is pushed upwards to avoid intersecting the TE)
	-Airfoil coordinate files can be either of the two common formats (Selig or Lednicer),
	 it is however recommended to have the LE strictly at (0, 0) and the TE at (1, 0). 
	 Do not include any header in the file, blank lines are fine in anywhere, use comma space or tab 
	 for separating the x and y coordinates. 