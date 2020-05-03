from fpdf import FPDF
from read_input import get_input



def write_pdf(inp, cl_max_airfoil, Delta_cl_max, flap_hinge_location):
    pdf = FPDF()
    pdf.add_page()
    size = 12
    pdf.set_font("Arial", "b", size=size)
    pdf.set_xy(20, 40-9)
    pdf.cell(200, size/2, txt="Input parameters:", ln=1, align='L')
    pdf.set_xy(100, 40-9)
    pdf.cell(200, size/2, txt="Output parameters:", ln=1, align='L')
    pdf.set_font("Arial", size=size)
    parameters = list(inp.__dict__.keys())
    units = ["m", "m", "", "", "m", "m", "deg", "deg", "x/c", "x/c", "y/b", "m", "", "deg", "m/s", "", ""]
    for i in range(len(parameters[0:parameters.index("colour")])):
        parm = parameters[i]
        value = " = "+str(inp.__getattribute__(parameters[i]))+" "+units[i]
        pdf.set_xy(20, 40+6*i)
        pdf.cell(200, size/2, txt=parm, ln=1, align='L')
        pdf.set_xy(55, 40+6*i)
        pdf.cell(200, size/2, txt=value, ln=1, align='L')

    names = ["cl_max_airfoil", "Delta_cl_max", "flap_hinge_location"]
    values = [round(cl_max_airfoil, 3), round(Delta_cl_max, 3), round(flap_hinge_location, 3)]
    for i in range(3):
        pdf.set_xy(100, 40+6*i)
        pdf.cell(200, size/2, txt=names[i], ln=1, align='L')
        pdf.set_xy(140, 40+6*i)
        pdf.cell(200, size/2, txt=" = "+str(values[i]), ln=1, align='L')

    # save the pdf with name .pdf
    pdf.output("pdf_out/out.pdf")


if __name__ == "__main__":
    inp = get_input("planforms/test_planform1.txt")
    write_pdf(inp, 1.2, 0.8, 0.5)