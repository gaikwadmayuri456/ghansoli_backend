from fastapi import APIRouter, Depends, HTTPException
import psycopg2.extras
from pydantic import BaseModel
from main import get_influx2_client
# from . import get_raw_db
# from sqlalchemy.orm import Session
# from loguru import logger
# import influxdb_client


router = APIRouter()

class GetInputData(BaseModel):
    devicecode: list
    zone: str
    measurment: str
@router.post("/showtemp", tags=["Temp"])

async def get_all_data(
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
                queryhandle = queryhandle + 'r["device_code"]== "' + i+'"'
                continue
            queryhandle = queryhandle + 'r["device_code"]== "' + i + '" or '
            count = count + 1
        q = f'''
         from(bucket: "data")
  |> range(start: 2023-03-01T00:00:00Z, stop: 2023-03-01T23:59:59Z)
  |> filter(fn: (r) => r["_measurement"] == "{data.measurment}")
  |> filter(fn: (r) => r["panel_no"] == "iam-gw-210104")
  |> filter(fn: (r) => r["device_code"] == "{data.devicecode}")
  |> filter(fn: (r) => r["zone"] == "{data.zone}")
  |> aggregateWindow(every:1mo, fn: max, createEmpty: false)
  |> yield(name: "max")
        '''

        q2 = f'''
        from(bucket:"data") 
        |> range(start: 2023-03-01T00:00:00Z, stop: 2023-03-01T23:59:59Z)
   |> filter(fn: (r) => r["_measurement"] == "{data.measurment}")
  |> filter(fn: (r) => r["panel_no"] == "iam-gw-210104")
  |> filter(fn: (r) => {queryhandle})
  |> filter(fn: (r) => r["zone"] == "{data.zone}")
      |> timeShift(duration: 330m, columns: ["_time"])
       |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
        |> yield(name: "last")
        '''
        result = client.query_api().query(query=q2)

        for x in result:
            mydata.append(x.records)
        # return mydata
    except Exception as e:
        # logger.critical(f'{e}')
        print("Exception is", e)
    finally:
        # print(devicecode,zone,measurment)
        return mydata


