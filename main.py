from datetime import datetime
from fastapi import FastAPI
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uvicorn import run
from loguru import logger
import influxdb_client
from starlette.middleware.cors import CORSMiddleware
from os import getenv

# from src.routes.all_routes import router
app = FastAPI(
    title='Ghansoli Backend'
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


def get_influx2_client():
    try:
        client = influxdb_client.InfluxDBClient(
            url=getenv("INFLUX_URL"),
            username=getenv("INFLUX_USERNAME"),
            password=getenv("INFLUX_PASSWORD"),
            token=getenv("INFLUX_TOKEN"),
            org=getenv("INFLUX_ORG")
        )
        # print("Hii")
        return client
    except HTTPException as e:
        raise e

    except Exception as e:
        logger.debug(f"{e}")
        raise HTTPException(status_code=500, detail=f"{e}")


class GetInputData(BaseModel):
    devicecode: list
    zone: str
    measurment: str
    startdate = datetime.today().strftime('%Y-%m-%dT00:00:00Z')
    endtdate = datetime.today().strftime('%Y-%m-%dT23:59:59Z')
    # startdate="2023-02-01T00:00:00Z"
    # endtdate = "2023-03-17T23:59:59Z"
#

@app.post("/showtemperature")
def get_all_data(
        data: GetInputData
):
    mydata = []
    try:
        client = get_influx2_client()
        query_api = client.query_api()
        resvar = client.organizations_api().find_organizations(org='iam')
        queryhandle = ''
        count = 0
        for i in data.devicecode:
            if len(data.devicecode) - 1 == count:
                queryhandle = queryhandle + 'r["device_code"]== "' + i + '"'
                continue
            queryhandle = queryhandle + 'r["device_code"]== "' + i + '" or '
            count = count + 1
        q = f'''
                from(bucket: "data")
          |> range(start: {data.startdate}, stop: {data.endtdate})
          |> filter(fn: (r) => r["_measurement"] == "{data.measurment}")
          |> filter(fn: (r) => r["panel_no"] == "iam-gw-210104")
          |> filter(fn: (r) => {queryhandle})
          |> filter(fn: (r) => r["device_code"] == "{data.devicecode}")
          |> filter(fn: (r) => r["zone"] == "{data.zone}")
           |> timeShift(duration: 330m, columns: ["_time"])
          |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
                '''

        q2 = f'''
        from(bucket:"data") 
    |> range(start: {data.startdate}, stop: {data.endtdate})
   |> filter(fn: (r) => r["_measurement"] == "{data.measurment}")
  |> filter(fn: (r) => r["panel_no"] == "iam-gw-210104")
  |> filter(fn: (r) => {queryhandle})
  |> filter(fn: (r) => r["zone"] == "{data.zone}")
  |> timeShift(duration: 330m, columns: ["_time"])
  |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
  |> yield(name: "last")
        '''

        q3 = f'''
  from(bucket: "data")
  |> range(start: 2023-03-17T00:00:00Z, stop: 2023-03-17T23:59:59Z)
  |> filter(fn: (r) => r["panel_no"] == "iam-gw-210105")
  |> filter(fn: (r) => r["_measurement"] == "misc")
  |> filter(fn: (r) => r["device_code"] == "MOD01")
  |> filter(fn: (r) => r["zone"] == "APF")
  |> yield(name: "last")
        
        '''
        q5=f'''
        
        from(bucket: "data")
  |> range(start: 2023-03-17T00:00:00Z, stop: 2023-03-17T23:59:59Z)
  |> filter(fn: (r) => r["panel_no"] == "iam-gw-210105")
  |> filter(fn: (r) => r["_measurement"] == "misc")
  |> filter(fn: (r) => r["device_code"] == "MOD07")
  |> filter(fn: (r) => r["zone"] == "OPSOU" or r["zone"] == "BATTCON")
  |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
  |> yield(name: "last")
        
        '''


        q6=f'''
        
        from(bucket: "data")
  |> range(start: 2023-03-17T00:00:00Z, stop: 2023-03-17T23:59:59Z)
  |> filter(fn: (r) => r["panel_no"] == "iam-gw-210105")
  |> filter(fn: (r) => r["_measurement"] == "misc")
  |> filter(fn: (r) => r["device_code"] == "MOD07")
  |> filter(fn: (r) => r["zone"] == "PLOAD1" or r["zone"] == "PLOAD2" or r["zone"] == "PLOAD3")
  |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
  |> yield(name: "last")
        '''

        q4= ''' SELECT last("value") FROM "power" WHERE ("panel_no"= 'iam-gw-210105' AND "device_code" = 'MOD01' AND "zone" = 'APF') AND "date"= datetime.today().strftime('%Y-%m-%dT00:00:00Z') '''
        # or r["zone"] == "PLOAD2" or r["zone"] == "PLOAD3"

        result = client.query_api().query(query=q4)

        for x in result:
            mydata.append(x.records)
        # return mydata
    except Exception as e:
        # logger.critical(f'{e}')
        print("Exception is", e)
    finally:
        # print(devicecode,zone,measurment)
        return mydata


if __name__ == "__main__":
    run("main:app", host="0.0.0.0", port=5019, reload=True)
