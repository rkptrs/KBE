from fpdf import FPDF
from read_input import get_input
import datetime


def write_list(pdf, title, position, names, values, units):
    pdf.set_font("Arial", "b", size=12)
    pdf.set_xy(position[0], position[1])
    pdf.cell(200, 6, txt=title, ln=1, align='L')
    pdf.set_font("Arial", size=12)

    for i in range(len(names)):
        value = " = "+str(values[i])+" "+units[i]
        pdf.set_xy(position[0], position[1]+10+6*i)
        pdf.cell(200, 6, txt=names[i], ln=1, align='L')
        pdf.set_xy(position[0]+40, position[1]+10+6*i)
        pdf.cell(200, 6, txt=value, ln=1, align='L')


def write_pdf(inp, cl_max_airfoil, Delta_cl_max, flap_hinge_location, planform_file_name, flap_deflection):
    pdf = FPDF()
    pdf.add_page()

    # Make title
    pdf.set_xy(20, 30)
    pdf.set_font("Arial", "b", size=14)
    title = "Sizing of high lift devices using Parapy: output file"
    pdf.cell(200, 6, txt=title, ln=1, align='L')

    # Write date
    pdf.set_xy(20, 40)
    pdf.set_font("Arial", size=12)
    date = "Saved at: " + str(datetime.datetime.today())
    pdf.cell(200, 6, txt=date, ln=1, align='L')

    # Write planform name
    pdf.set_xy(20, 46)
    name = "Planform file name: " + str(planform_file_name)
    pdf.cell(200, 6, txt=name, ln=1, align='L')

    list_y = 60

    # Make input list
    names = list(inp.__dict__.keys())
    names = names[0:names.index("colour")]
    values = []
    for i in range(len(names)):
        values.append(inp.__getattribute__(names[i]))
    units = ["m", "m", "", "", "m", "m", "deg", "deg", "x/c", "x/c", "y/b", "m", "", "deg", "m/s", "", ""]
    write_list(pdf, "Input parameters:", (20, list_y), names, values, units)

    # Make output list
    names = ["Cl_max of airfoil", "Delta Cl_max", "Flap hinge location", "Flap deflection"]
    values = [round(cl_max_airfoil, 3), round(Delta_cl_max, 3), round(flap_hinge_location, 3), round(flap_deflection, 3)]
    units = ["", "", "x/c", "deg"]
    write_list(pdf, "Output parameters:", (110, list_y), names, values, units)

    pdf.output("pdf_out/"+planform_file_name+"_"+str(datetime.datetime.today())[:10]+".pdf")


if __name__ == "__main__":
    inp = get_input("planforms/test_planform1.txt")
    write_pdf(inp, 1.2, 0.8, 0.5, "Test run", 45)
