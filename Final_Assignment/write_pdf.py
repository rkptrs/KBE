from fpdf import FPDF
from read_input import get_input
import datetime


# Function for writing a list of parameters in the format "name = Value unit" with a header at the beginning
def write_list(pdf, title, position, names, values, units):
    pdf.set_font("Arial", "b", size=12)             # bold font for title
    pdf.set_xy(position[0], position[1])            # set position
    pdf.cell(200, 6, txt=title, ln=1, align='L')    # write header
    pdf.set_font("Arial", size=12)                  # set font to normal

    for i in range(len(values)):                    # Round values to 4 dp
        v = values[i]
        if type(v) == float or str(type(v)) == "<class 'numpy.float64'>":
            values[i] = round(v, 4)

    for i in range(len(names)):                             # write all parameters in a loop
        value = " = "+str(values[i])+" "+units[i]           # combine value and unit in one string
        pdf.set_xy(position[0], position[1]+10+6*i)         # set position for name
        pdf.cell(200, 6, txt=names[i], ln=1, align='L')     # write name
        pdf.set_xy(position[0]+40, position[1]+10+6*i)      # set position for value + unit
        pdf.cell(200, 6, txt=value, ln=1, align='L')        # write value + unit


def write_pdf(inp, cl_max_airfoil, Delta_cl_max, flap_hinge_location, planform_file_name, flap_deflection, alpha_stall,
              flap_count, cl_input, mach, kink_chord, tip_chord, area, coordinates):
    pdf = FPDF()        # create a PDF and add a page
    pdf.add_page()

    # Make title of document
    pdf.set_xy(20, 30)                                                  # set location of cursor
    pdf.set_font("Arial", "b", size=14)                                 # set font to large bold
    title = "Sizing of high lift devices using Parapy: output file"
    pdf.cell(200, 6, txt=title, ln=1, align='L')                        # write title

    # Write date
    pdf.set_xy(20, 40)                                                  # location of cursor
    pdf.set_font("Arial", size=12)                                      # normal font
    date = "Saved at: " + str(datetime.datetime.today())                # get date and time
    pdf.cell(200, 6, txt=date, ln=1, align='L')                         # write

    # Write planform name same structure as above
    pdf.set_xy(20, 46)
    name = "Planform file name: " + str(planform_file_name)
    pdf.cell(200, 6, txt=name, ln=1, align='L')

    # Write type of analysis performed
    if cl_input is None:
        txt = "The HLDs were sized using the CL_max computed by external analysis using xfoil and AVL"
        txt2 = "External analysis was carried out"
    else:
        pdf.set_text_color(255, 0, 0)
        txt = "The HLDs were sized using the CL_max of the clean wing provided by the user in the main file."
        txt2 = "No external analysis was carried out."
    pdf.set_xy(20, 52)
    pdf.cell(200, 6, txt=txt, ln=1, align='L')
    pdf.set_xy(20, 58)
    pdf.cell(200, 6, txt=txt2, ln=1, align='L')
    pdf.set_text_color(0, 0, 0)

    list_y = 70

    # Make input list
    names = list(inp.__dict__.keys())               # get all the input parameter attribute names
    names = names[0:names.index("colour")]          # crop the last two parameters which are "color" and "valid"
    values = []
    for i in range(len(names)):                             # use the attribute names to get all the variables in a list
        values.append(inp.__getattribute__(names[i]))
    units = ["m", "m", "", "", "m", "m", "deg", "deg", "x/c", "x/c", "y/b", "m", "", "deg", "m/s", "", "", ""]
    write_list(pdf, "Input parameters:", (20, list_y), names, values, units)        # call the function defined above

    # Make output list
    names = ["Cl_max clan", "Delta Cl_max", "Flap hinge location", "Flap deflection", "Stall AoA", "Flaps per wing",
             "Flapped wing area"]
    values = [cl_max_airfoil, Delta_cl_max, flap_hinge_location, flap_deflection, alpha_stall, flap_count, area]
    units = ["", "", "x/c", "deg", "deg", "", "m^2"]
    write_list(pdf, "Output parameters:", (110, list_y), names, values, units)

    # Other parameters list
    names = ["Mach number", "Kink chord", "Tip chord"]
    values = [mach, kink_chord, tip_chord]
    units = ["", "m", "m"]
    write_list(pdf, "Other parameters", (110, 140), names, values, units)

    # Write airfoil below
    pdf.set_xy(20, 190)
    pdf.set_font("Arial", "b", size=12)
    name = "Cross section of airfoil with the flap system:"
    pdf.cell(200, 6, txt=name, ln=1, align='L')

    # Draw airfoil
    x, y = [], []
    for section in coordinates:             # go through coordinates to find maximums for normalization
        for i in range(len(section)):
            x.append(section[i][0])
            y.append(section[i][1])
    xs = min(x)
    ys = max(y)
    chord = max(x) - xs

    for section in coordinates:
        x, y = [], []
        for i in range(len(section)):               # normalize coordinates
            x.append((section[i][0] - xs)/chord)
            y.append((section[i][1] - ys)/chord)

        for i in range(len(x)-1):
            x0, y0 = 30, 210
            factor = 150                            # size of airfoil in pixels
            x1 = x[i]*factor
            y1 = y[i]*factor
            x2 = x[i+1]*factor
            y2 = y[i+1]*factor
            pdf.line(x0+x1, y0-y1, x0+x2, y0-y2)    # draw line between all consecutive coordinates

    # save PDF into the appropriate folder, name includes input planform name and date for some organization
    pdf.output("pdf_out/"+planform_file_name+"_"+str(datetime.datetime.today())[:10]+".pdf")

if __name__ == "__main__":
    inp = get_input("planforms/test_planform1.txt")
    write_pdf(inp, 1.2, 0.8, 0.5, "Test run", 45)
