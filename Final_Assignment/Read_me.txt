--To run the application without adjusting anything:--

Start the application by running the Main.py file.
    A Parapy GUI opens, with a tree in the left top corner. Double click the 'HLD sizing application (root)' label.
    A progress bar will open, showing the progress of the Xfoil analysis. After the progress bar closes, the AVL analysis
    needs a little while longer, after which the aircraft will appear, showing the sized flaps.

--To make changes before running the application:--

The planforms folder contains a number of example input files. These input files contain the geometry of the aircraft,
    the required maximum lift coefficient of the flapped aircraft and the flight conditions at which the maximum lift coefficient
    should be attained. These values in these planform files can be changed, or a new planform file can be added, adhering to
    the structure of the existing planform files. Some instructions can be found in the READ_ME of the planforms folder.

The program_files contains three txt files that should not be altered. The second and third file in this folder form
    the upper and lower bounds to the values in the planform files. Once the Main.py file is run, the values in the planform
    file are checked to make sure they are not outside of these bounds. If they are outside the bounds, an error message will
    appear and the app will use the default planform, which is the first file in the program_files folder.

If a new planform file is created, its name should be inserted in the Main.py file. This can be done under the 'planform_file_name' slot.
    Underneath that slot is also the option to set the cl_max of the clean wing. This option bypasses the Xfoil and AVL analysis.
    This was done to be able to quickly access the GUI without having to wait for the analyses. Setting this option to 'None'
    will make the app use the Xfoil and AVL analyses to determine the cl_max of the clean wing.
    The third option situated in the Model class is to hide the left wing, which is a mirror of the right wing.
    The last option presented is the position of the wing, which can be low, mid or high.

Lastly, some of the input parameters for hld design have been set to defaults. These include the take-off/landing
    conditions and the maximum deflection angle of the flaps. The air density has been set to 1.225 kg/m^3 and the maximum
    deflection angle has been set at 45 degrees. These are representative values for real world scenarios and were put in
    place to limit the required user input. The values can easily be changed by the user, but for now they are set constant.


Some notes for the airfoil files:

	-In order to ensure a good quality of the geometry, the minimum required amount of airfoil coordinates is 50.
	    If a lower number is given as input, an error is raised.
	-Fowler flaps can not be used with cusp trailing edges. If such an airfoil is given as input, the calculations will
	    still work, but the application will not output a valid geometry.
	-Airfoil coordinate files can be either of the two common formats (Selig or Lednicer),
	    it is however recommended to have the LE strictly at (0, 0) and the TE at (1, 0).
	    Do not include any header in the file, blank lines are fine anywhere, use comma space or tab
	    for separating the x and y coordinates.