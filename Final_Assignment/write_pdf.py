from fpdf import FPDF
from read_input import get_input
import datetime


# Function for writing a list of parameters in the format "name = Value unit" with a header at the beginning
def write_list(pdf, title, position, names, values, units):
    pdf.set_font("Arial", "b", size=12)             # bold font for title
    pdf.set_xy(position[0], position[1])            # set position
    pdf.cell(200, 6, txt=title, ln=1, align='L')    # write header
    pdf.set_font("Arial", size=12)                  # set font to normal

    for i in range(len(names)):                             # write all parameters in a loop
        value = " = "+str(values[i])+" "+units[i]           # combine value and unit in one string
        pdf.set_xy(position[0], position[1]+10+6*i)         # set position for name
        pdf.cell(200, 6, txt=names[i], ln=1, align='L')     # write name
        pdf.set_xy(position[0]+40, position[1]+10+6*i)      # set position for value + unit
        pdf.cell(200, 6, txt=value, ln=1, align='L')        # write value + unit


def write_pdf(inp, cl_max_airfoil, Delta_cl_max, flap_hinge_location, planform_file_name, flap_deflection):
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

    list_y = 60

    # Make input list
    names = list(inp.__dict__.keys())               # get all the input parameter attribute names
    names = names[0:names.index("colour")]          # crop the last two parameters which are "color" and "valid"
    values = []
    for i in range(len(names)):                             # use the attribute names to get all the variables in a list
        values.append(inp.__getattribute__(names[i]))
    units = ["m", "m", "", "", "m", "m", "deg", "deg", "x/c", "x/c", "y/b", "m", "", "deg", "m/s", "", ""]
    write_list(pdf, "Input parameters:", (20, list_y), names, values, units)        # call the function defined above

    # Make output list
    names = ["Cl_max of airfoil", "Delta Cl_max", "Flap hinge location", "Flap deflection"]
    values = [round(cl_max_airfoil, 3), round(Delta_cl_max, 3), round(flap_hinge_location, 3), round(flap_deflection, 3)]
    units = ["", "", "x/c", "deg"]
    write_list(pdf, "Output parameters:", (110, list_y), names, values, units)

    # save PDF into the appropriate folder, name includes input planform name and date for some organization
    pdf.output("pdf_out/"+planform_file_name+"_"+str(datetime.datetime.today())[:10]+".pdf")


if __name__ == "__main__":
    inp = get_input("planforms/test_planform1.txt")
    write_pdf(inp, 1.2, 0.8, 0.5, "Test run", 45)
