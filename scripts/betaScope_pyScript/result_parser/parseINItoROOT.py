import ROOT
import os
from array import array
from parseBetaResultsToExcel import *
from ROOTFile import RootFile
from daq_info import DAQInfo
from get_time_res import Get_Time_Resolution
import logging, coloredlogs

import sys
sys.path.append('/home/datataking/HGTD_BetaScope_FW_Test/scripts/UDI_reader/')
from UDI_reader import UDI_reader

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=log)


def ParseINItoROOT(fname="_results.ini"):
    data_ini = configparser.ConfigParser()
    data_ini.read(fname)
    data_ini_section = data_ini.sections()
    log.info(data_ini_section)

    dut_trig = ["DUT"]

    # look for description file generated by the DAQ
    description_file = DAQInfo()
    for descr in os.listdir("./"):
        if "_Description.ini" in descr:
            description_file = DAQInfo.open(descr)
            log.info("found DAQ description file")
            break

    sensor_name = description_file.full_name

    # total transipedence (include amp)
    resistance = 4700

    # Get PiN charge
    try:
        UDI_number = description_file.dut_udi
        reader = UDI_reader()
        pin_charge = reader.get_pin_charge(UDI_number)
    except:
        pin_charge = 0.

    my_trig_name = description_file.trig_name.lower()
    if "hpk" in my_trig_name and "s8664" in my_trig_name:
        my_trig_name = "hpks8664"

    res50_result = Get_Time_Resolution(
        f"run_info_v{os.environ['RUN_INFO_VER']}.ini",
        "50",
        description_file.scope.lower(),
        my_trig_name,
        description_file.run_number,
    )

    res20_result = Get_Time_Resolution(
        f"run_info_v{os.environ['RUN_INFO_VER']}.ini",
        "20",
        description_file.scope.lower(),
        my_trig_name,
        description_file.run_number,
    )

    res_tmax = Get_Time_Resolution(
        f"run_info_v{os.environ['RUN_INFO_VER']}.ini",
        "tmax",
        description_file.scope.lower(),
        my_trig_name,
        description_file.run_number,
    )

    res_fit_tmax = Get_Time_Resolution(
        f"run_info_v{os.environ['RUN_INFO_VER']}.ini",
        "fit_tmax",
        description_file.scope.lower(),
        my_trig_name,
        description_file.run_number,
    )

    res_zerox_tmax = Get_Time_Resolution(
        f"run_info_v{os.environ['RUN_INFO_VER']}.ini",
        "zero_cross_tmax",
        description_file.scope.lower(),
        my_trig_name,
        description_file.run_number,
    )

    leakage_data = Read_Current(f"run_info_v{os.environ['RUN_INFO_VER']}.ini")

    for ch in dut_trig:
        rowCounter = 1

        output_file = RootFile(
            "_results.root",
            f"run{description_file.run_number}",
            #f"{os.getcwd()}/_results.ini",
            os.getcwd().split("/")[5]
        )
        for par in INI_TO_EXCEL.keys():
            if "sensor_name" in par:
                output_file.create_char_branch(par)
                output_file.set_char_branch_value(par, sensor_name)
            elif "run_number" in par:
                output_file.create_branch(par, "i")
            elif "time_resolution" in par:
                output_file.create_branch(par, "d")
            else:
                if INI_TO_EXCEL[par][0] == None:
                    continue
                output_file.create_branch(par, "d")

        for bias in data_ini_section:
            myRunNum = f"{description_file.run_number}->{rowCounter}"
            if ch in bias:
                run_header = bias.split(",")
                Bias = run_header[1].replace("V", "")
                cycle = run_header[2]
                for par in INI_TO_EXCEL.keys():
                    if par == "sensor_name":
                        continue
                    elif par == "run_number":
                        continue
                    elif par == "temperature":
                        try:
                            Temp = config[bias]["temperature"]
                        except:
                            Temp = "-30"
                        output_file.set_branch_value(par, float(Temp))
                    elif par == "bias_voltage":
                        output_file.set_branch_value(par, float(Bias))
                    elif par == "cycle":
                        output_file.set_branch_value(par, float(cycle))
                    elif par == "resistance":
                        output_file.set_branch_value(par, float(resistance))
                    elif par == "pin_charge":
                        output_file.set_branch_value(par, float(pin_charge))
                    elif par == "time_resolution_50":
                        output_file.set_branch_value(
                            par, res50_result[(float(Bias), int(cycle))][3]
                        )
                    elif par == "time_resolution_50_err":
                        output_file.set_branch_value(
                            par, res50_result[(float(Bias), int(cycle))][4]
                        )
                    elif par == "time_resolution_20":
                        output_file.set_branch_value(
                            par, res20_result[(float(Bias), int(cycle))][3]
                        )
                    elif par == "time_resolution_20_err":
                        output_file.set_branch_value(
                            par, res20_result[(float(Bias), int(cycle))][4]
                        )
                    elif "time_resolution_tmax" in par:
                        if res_tmax is None:
                            continue
                        else:
                            if "err" in par:
                                output_file.set_branch_value(
                                    par, res_tmax[(float(Bias), int(cycle))][4]
                                )
                            else:
                                output_file.set_branch_value(
                                    par, res_tmax[(float(Bias), int(cycle))][3]
                                )
                    elif "time_resolution_fit_tmax" in par:
                        if res_fit_tmax is None:
                            continue
                        else:
                            if "err" in par:
                                output_file.set_branch_value(
                                    par, res_fit_tmax[(float(Bias), int(cycle))][4]
                                )
                            else:
                                output_file.set_branch_value(
                                    par, res_fit_tmax[(float(Bias), int(cycle))][3]
                                )
                    elif "time_resolution_zero_x_tmax" in par:
                        if res_zerox_tmax is None:
                            continue
                        else:
                            if "err" in par:
                                output_file.set_branch_value(
                                    par, res_zerox_tmax[(float(Bias), int(cycle))][4]
                                )
                            else:
                                output_file.set_branch_value(
                                    par, res_zerox_tmax[(float(Bias), int(cycle))][3]
                                )
                    elif par == "leakage":
                        output_file.set_branch_value(
                            par, leakage_data[(float(Bias), int(cycle))][3]
                        )
                    else:
                        data_ini_key = INI_TO_EXCEL[par][0]
                        if data_ini_key == None:
                            continue
                        try:
                            value = data_ini[bias][data_ini_key]
                            output_file.set_branch_value(par, float(value))
                        except:
                            continue
            else:
                continue
            output_file.fill()


def parseINItoROOT2(fileout, title="Hi", run_folder="./", fname="_results.ini"):
    fileout.cd()
    config = configparser.ConfigParser()
    config.read(fname)
    config_section = config.sections()
    # print(config_section)

    description_file = None
    try:
        for descr in os.listdir(run_folder):
            if "_Description.ini" in descr:
                description_file = configparser.ConfigParser()
                description_file.read(descr)
                print("found DAQ description file")
                break
    except Exception as e:
        print(Exception)

    dut_trig = ["DUT"]

    branches = {}

    print(title)
    RunNum = title.split("_")[1]
    SensorName = title
    trigBias = 395
    Temp = 0

    if "_20C" in title:
        Temp = 20
        trigBias = 420
    if "_neg30C" in title:
        trigBias = 390
        Temp = -30
    if "_neg20C" in title:
        Temp = -20
    if "_neg10C" in title:
        Temp = -10

    if description_file:
        try:
            RunNum = description_file["Run_Description"]["Run_Number"]
            SensorName = description_file["Run_Description"]["DUT_Senor_Name"]
            SensorName += (
                "-Fluence "
                + description_file["Run_Description"]["DUT_Fluence_Type"]
                + "-"
                + description_file["Run_Description"]["DUT_Fluence"]
            )
            SensorName += (
                "--"
                + description_file["Run_Description"]["DUT_Readout_Board"]
                + "-"
                + description_file["Run_Description"]["DUT_Readout_Board_Number"]
            )

            Temp = description_file["Run_Description"]["Temperature"]
            trigBias = description_file["Run_Description"]["Trigger_Voltage"]
        except Exception as e:
            print(Exception)

    Resistance = 4700

    # Get PiN charge
    try:
        UDI_number = description_file.dut_udi
        reader = UDI_reader()
        pin_charge = reader.get_pin_charge(UDI_number)
    except:
        pin_charge = 0.

    for ch in dut_trig:
        rowCounter = 1
        # print RunNum, title
        ttree = ROOT.TTree(str(RunNum), title)
        for par in INI_TO_EXCEL.keys():
            if "SensorName" in par:
                branches[par] = array("b").frombytes(str(SensorName).encode())
                ttree.Branch(par, branches[par], f"{par}/C")
            elif "runNumber" in par:
                continue
            else:
                branches[par] = array("d", [0])
                ttree.Branch(par, branches[par], f"{par}/D")

        for bias in config_section:
            myRunNum = str(RunNum) + "->" + str(rowCounter)
            if ch in bias:
                if ch != "Trig":
                    run_header = bias.split(",")
                    Bias = run_header[1].replace("V", "")
                    cycle = run_header[2]
                else:
                    try:
                        SensorName = description_file["Run_Description"][
                            "Trigger_Sensor_Name"
                        ]
                    except:
                        pass
                    Bias = config[bias]["trigger_bias"]
                    run_header = bias.split(",")
                    cycle = run_header[2]
                for par in par_list:
                    if par == "SensorName":
                        continue
                    elif par == "runNumber":
                        continue
                    elif par == "Temp":
                        try:
                            Temp = config[bias]["temperature"]
                        except:
                            Temp = "-30"
                        branches[par][0] = float(Temp)
                    elif par == "Bias":
                        branches[par][0] = float(Bias)
                    elif par == "cycle":
                        branches[par][0] = float(cycle)
                    elif par == "Resistance":
                        branches[par][0] = float(Resistance)
                    elif par == "pin_charge":
                        branches[par][0] = float(pin_charge)
                    else:
                        try:
                            branches[par][0] = float(config[bias][par])
                        except:
                            branches[par][0] = 0

            ttree.Fill()

        ttree.Write()  # "run"+str(RunNum), ROOT.TObject.kOverwrite)


def ParseRawINIToROOT(filename="raw_results.ini"):
    config = configparser.ConfigParser()
    config.read(filename)
    output_file = RootFile("raw_results.root", "raw")
    created_branches = False
    for sec in config.sections():
        if not created_branches:
            for key in config[sec]:
                output_file.create_branch(key, "d")
            output_file.create_branch("bias", "d")
            output_file.create_branch("cycle", "i")
            created_branches = True
        for key in config[sec]:
            output_file[key][0] = float(config[sec][key])
        run_header = sec.split(",")
        output_file["bias"][0] = float(run_header[0].replace("V", ""))
        cycle = int(run_header[1])
        output_file.fill()


if __name__ == "__main__":
    ParseINItoROOT()
    ParseRawINIToROOT()
