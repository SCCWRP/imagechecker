import pandas as pd
import re
from math import log10
from .functions import checkData, convert_dtype, fetch_meta, check_precision, check_length, check_scale


def checkDataTypes(dataframe, tablename, eng, meta, *args, output = None, **kwargs):
    
    ret = [ 
        checkData(
            dataframe = dataframe,
            tablename = tablename,
            badrows = [
                {
                    'row_number': int(rownum),
                    'value': val if not pd.isnull(val) else '',
                    'message': msg
                } 
                for rownum, val, msg in
                dataframe[
                    dataframe[col].apply(
                        lambda x:
                        # function returns True if it successfully converted
                        # We negate to get the cases where it was not successfully converted
                        not convert_dtype(
                            # using the meta dataframe we can get the python datatype
                            meta.iloc[
                                meta[
                                    meta.column_name == col
                                ].index, 
                                meta.columns.get_loc("dtype")
                            ] \
                            .values[0]
                            ,
                            x
                        )
                    )
                ] \
                .apply(
                    lambda row:
                    (
                        row.name,
                        row[col], 
                        "the value here {} is an invalid value for the column {} of datatype {}" \
                        .format(
                            row[col],
                            col,
                            meta.iloc[
                                meta[meta.column_name == col].index, 
                                meta.columns.get_loc("data_type")
                            ].values[0]
                        )
                    ),
                    axis = 1
                ) \
                .values
            ],
            badcolumn = col,
            error_type = "Invalid Datatype",
            is_core_error = True,
            error_message = "The value here is not valid for the datatype {}" \
                .format(
                    meta.iloc[
                        meta[meta.column_name == col].index, 
                        meta.columns.get_loc("data_type")
                    ].values[0]
                )
        )
        for col in dataframe.columns
    ]

    if output:
        output.put(ret)
    return ret
    

def checkPrecision(dataframe, tablename, eng, meta, *args, output = None, **kwargs):
        
    ret = \
    [
        checkData(
            dataframe = dataframe,
            tablename = tablename,
            badrows = [
                {
                    'row_number': int(rownum),
                    'value': val if not pd.isnull(val) else '',
                    'message': msg
                }
                for rownum, val, msg in
                dataframe[
                    dataframe[col].apply(
                        lambda x:

                        not check_precision(
                            x,
                            meta.iloc[
                                meta[
                                    meta.column_name == col
                                ].index, 
                                meta.columns.get_loc("numeric_precision")
                            ] \
                            .values[0]
                        )
                    )
                ] \
                .apply(
                    lambda row:
                    (
                        row.name,
                        row[col], 
                        "the value here {} is too long for the column {} which allows {} significant digits" \
                        .format(
                            row[col],
                            col,
                            meta.iloc[
                                meta[meta.column_name == col].index, 
                                meta.columns.get_loc("numeric_precision")
                            ].values[0]
                        )
                    ),
                    axis = 1
                ) \
                .values
            ],
            badcolumn = col,
            error_type = "Value too long",
            is_core_error = True,
            error_message = "the value here is too long for the column {} which allows {} significant digits" \
                .format(
                    col,
                    int(
                        meta.iloc[
                            meta[meta.column_name == col].index, 
                            meta.columns.get_loc("numeric_precision")
                        ].values[0]
                    )
                )
        )
        for col in dataframe.columns if col in meta[meta.udt_name == 'numeric'].column_name.values
    ]

    if output:
        output.put(ret)
    return ret

def checkScale(dataframe, tablename, eng, meta, *args, output = None, **kwargs):

    ret = \
    [
        checkData(
            dataframe = dataframe,
            tablename = tablename,
            badrows = [
                {
                    'row_number': int(rownum),
                    'value': val if not pd.isnull(val) else '',
                    'message': msg
                }
                for rownum, val, msg in
                dataframe[
                    dataframe[col].apply(
                        lambda x:

                        not check_scale(
                            x,
                            meta.iloc[
                                meta[
                                    meta.column_name == col
                                ].index, 
                                meta.columns.get_loc("numeric_scale")
                            ] \
                            .values[0]
                        )
                    )
                ] \
                .apply(
                    lambda row:
                    (
                        row.name,
                        row[col], 
                        """the value here {} 
                        has too many decimal places for the column {} 
                        which allows {} decimal places""" \
                        .format(
                            row[col],
                            col,
                            meta.iloc[
                                meta[meta.column_name == col].index, 
                                meta.columns.get_loc("numeric_scale")
                            ].values[0]
                        )
                    ),
                    axis = 1
                ) \
                .values
            ],
            badcolumn = col,
            error_type = "Value too long",
            is_core_error = True,
            error_message = "The value here has too many decimal places (should have a maximum of {} decimal places)" \
                .format(
                    int(
                        meta.iloc[
                            meta[meta.column_name == col].index, 
                            meta.columns.get_loc("numeric_scale")
                        ].values[0]
                    )
                )
        )
        for col in dataframe.columns if col in meta[meta.udt_name == 'numeric'].column_name.values
    ]

    if output:
        output.put(ret) 
    return ret


def checkLength(dataframe, tablename, eng, meta, *args, output = None, **kwargs):
    
    ret = \
    [
        checkData(
            dataframe = dataframe,
            tablename = tablename,
            badrows = [
                {
                    'row_number': int(rownum),
                    'value': val if not pd.isnull(val) else '',
                    'message': msg
                }
                for rownum, val, msg in
                dataframe[
                    dataframe[col].apply(
                        lambda x:
                        not check_length(
                            x
                            ,
                            meta.iloc[
                                meta[
                                    meta.column_name == col
                                ].index, 
                                meta.columns.get_loc("character_maximum_length")
                            ] \
                            .values[0]
                               
                        )
                    )
                ] \
                .apply(
                    lambda row:
                    (
                        row.name,
                        row[col], 
                        "the value here {} has too many characters for the column {} which has a {} character limit" \
                        .format(
                            row[col],
                            col,
                            meta.iloc[
                                meta[meta.column_name == col].index, 
                                meta.columns.get_loc("character_maximum_length")
                            ].values[0]
                        )
                    ),
                    axis = 1
                ) \
                .values
            ],
            badcolumn = col,
            error_type = "Value too long",
            is_core_error = True,
            error_message = "The value here has too many characters, while the character limit is {}" \
                .format(
                    meta.iloc[
                        meta[meta.column_name == col].index, 
                        meta.columns.get_loc("character_maximum_length")
                    ].values[0]
                )
        )
        for col in dataframe.columns if col in meta[~pd.isnull(meta.character_maximum_length)].column_name.values
    ]

    if output:
        output.put(ret) 
    return ret



def checkNotNull(dataframe, tablename, eng, meta, *args, output = None, **kwargs):

    ret = \
    [
        checkData(
            dataframe = dataframe,
            tablename = tablename,
            badrows = [
                {
                    'row_number': int(rownum),
                    'value': val if not pd.isnull(val) else '',
                    'message': msg
                }
                for rownum, val, msg in
                dataframe[
                    dataframe[col].apply(
                        lambda x:
                        True if ((pd.isnull(x)) or (x == '')) else False
                    )
                ] \
                .apply(
                    lambda row:
                    (
                        row.name,
                        row[col], 
                        f"There is an empty value here, but the column {col} requires a value in all rows"
                    ),
                    axis = 1
                ) \
                .values
            ],
            badcolumn = col,
            error_type = "Missing Required Data",
            is_core_error = True,
            error_message = f"There is an empty value here, but the column {col} requires a value in all rows"
        )
        for col in dataframe.columns if col in meta[meta.is_nullable == 'NO'].column_name.values
    ]

    if output:
        output.put(ret) 

    return ret



def checkIntegers(dataframe, tablename, eng, meta, *args, output = None, **kwargs):
        
    ret = \
    [
        checkData(
            dataframe = dataframe,
            tablename = tablename,
            badrows = [
                {
                    'row_number': int(rownum),
                    'value': val if not pd.isnull(val) else '',
                    'message': msg
                }
                for rownum, val, msg in
                dataframe[
                    dataframe[col].apply(
                        lambda x:
                        False if pd.isnull(x)
                        else not ( (x >= -32768) & (x <= 32767) )
                        if meta.iloc[meta[meta.column_name == col].index, meta.columns.get_loc("udt_name")].values[0] == 'int2'
                        else not ( (x >= -2147483648) & (x <= 2147483647) )
                        if meta.iloc[meta[meta.column_name == col].index, meta.columns.get_loc("udt_name")].values[0] == 'int4'
                        else not ( (x >= -9223372036854775808) & (x <= 9223372036854775807) )
                        if meta.iloc[meta[meta.column_name == col].index, meta.columns.get_loc("udt_name")].values[0] == 'int8'
                        
                        # if something else slips through the cracks, this will not allow it through by default
                        else True 
                    )
                ] \
                .apply(
                    lambda row:
                    (
                        row.name,
                        row[col], 
                        "The column {} allows integer values from {}" \
                        .format(
                            col,
                             "-32768 to 32767"
                            if meta.iloc[meta[meta.column_name == col].index, meta.columns.get_loc("udt_name")].values[0] == 'int2'
                            else  "-2147483648 to 2147483647"
                            if meta.iloc[meta[meta.column_name == col].index, meta.columns.get_loc("udt_name")].values[0] == 'int4'
                            else  "-9223372036854775808 to 9223372036854775807"
                            if meta.iloc[meta[meta.column_name == col].index, meta.columns.get_loc("udt_name")].values[0] == 'int8'

                            # It should never be anything other than the above cases, since below we are filtering for int2, 4, and 8 columns.
                            else "(unexpected error occurred. If you see this, contact it@sccwrp.org)"
                        )
                    ),
                    axis = 1
                ) \
                .values
            ],
            badcolumn = col,
            error_type = "Value out of range",
            is_core_error = True,
            error_message = "The column {} allows integer values from {}" \
                .format(
                    col,
                    "-32768 to 32767"
                    if meta.iloc[meta[meta.column_name == col].index, meta.columns.get_loc("udt_name")].values[0] == 'int2'
                    else  "-2147483648 to 2147483647"
                    if meta.iloc[meta[meta.column_name == col].index, meta.columns.get_loc("udt_name")].values[0] == 'int4'
                    else  "-9223372036854775808 to 9223372036854775807"
                    if meta.iloc[meta[meta.column_name == col].index, meta.columns.get_loc("udt_name")].values[0] == 'int8'

                    # It should never be anything other than the above cases, since below we are filtering for int2, 4, and 8 columns.
                    else "(unexpected error occurred. If you see this, contact it@sccwrp.org)"
                )
        )
        for col in dataframe.columns if col in meta[meta.udt_name.isin(['int2','int4','int8'])].column_name.values
    ]

    if output:
        output.put(ret)
    return ret