# -*- coding: utf-8 -*-

import plotly.graph_objects as go
import argparse
import datetime
import numpy as np
from plotly.subplots import make_subplots
import math
import json
import os
from copy import deepcopy
from PIL import Image

font = dict(family='SimHei', size=18)

# set command line argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str)
parser.add_argument("save_dir", type=str)
args = parser.parse_args()
filename = args.filename
save_dir = args.save_dir

x = []
y = []
z = []

def read_data_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"File {file_path} not found")
        return None
    except json.JSONDecodeError:
        print(f"File {file_path} is not in regular format")
        return None

# read data file
data = read_data_file(filename)

if data:
    x = data.get('x', [])
    y = data.get('y', [])
    z = data.get('z', [])

# A4 Size (in inches) horizontal
dpi = 300
a4_width_inches = 11.69
a4_height_inches = 8.27
a4_width_pixels = a4_width_inches * dpi
a4_height_pixels = a4_height_inches * dpi

unit_height = len(y)
unit_width = len(x)

# Calculate the unit pixel size
pixel_per_unit = 12

# Calculate the pixel size of the heat map
heatmap_width_pixels = unit_width * pixel_per_unit
heatmap_height_pixels = unit_height * pixel_per_unit

data_array = np.array(z, dtype=np.float64)

# Calculate the number of elements after padding
num_elements = int(np.ceil(data_array.shape[1] * 3 / a4_width_pixels) * a4_width_pixels / 3) - data_array.shape[1]
padding_array = np.full((data_array.shape[0], num_elements), 0)
data_array = np.concatenate((data_array, padding_array), axis=1)

rows = math.ceil(data_array.shape[1] * 3 / a4_width_pixels)

# default font size
font_size = 24
title_font_size = 18 * 3
colorbar_thickness = 20 
num_rows, num_cols = data_array.shape
print('Shape', data_array.shape)
heatmap_width = pixel_per_unit * num_cols
heatmap_height = pixel_per_unit * num_rows

heatmap_height_total = 0
plots = []

create_subplots = math.ceil(a4_height_pixels / heatmap_height)

fig = make_subplots(rows=create_subplots , cols=1)

idex = 0
png_idx=1
is_colorbar_showscale = True
image_paths = []

start_values = [(data_array.shape[1] / rows) * i for i in range(rows)]
end_values = [start + (data_array.shape[1] / rows) for start in start_values]

# Add heatmap to subplots
for i in range(rows):
    start = start_values[i]
    end = end_values[i]
    print('start', start)
    print('end', end)
    
    current_x = x[int(start):int(end)]
    heatmap = go.Heatmap(
        hoverinfo='x+y+z',
        z=data_array[:, int(start):int(end)],
        x=current_x,
        y=y,
        colorscale=[[0, 'rgb(0,0,255)'], [0.5, 'rgb(255,255,255)'], [1, 'rgb(255,0,0)']],
        zmid=0,
        zmin=-0.5,
        zmax=0.5,
        zsmooth='best',
        showscale=is_colorbar_showscale,
        colorbar=dict(
            x=0.5,
            y=1.2,
            len=0.6,
            xanchor='center',
            yanchor='top',
            orientation='h',
            thickness=colorbar_thickness,
            tickfont=dict(size=title_font_size),
            title=dict(
                text='误差刻度:',
                side='right',
                font=dict(
                    size=title_font_size,
                    color='green'
                )
            )
        )
    )
    is_colorbar_showscale = False
    # if png_idx > 1:
        # margin=dict(
        #     # l=50,
        #     # r=50,
        #     # b=50,
        #     t=500,
        #     # pad=10
        # ),
        # heatmap['colorbar']=dict(
        #     x=0.5,
        #     y=1.2,
        #     len=0.6,
        #     xanchor='center',
        #     yanchor='top',
        #     orientation='h',
        #     # bgcolor='rgba(0,0,0,0)',
        #     thickness=20,
        #     tickfont=dict(size=font_size, color='rgba(0,0,0,0)'),  # Set color to transparent
        #     title=dict(
        #         text='',
        #         side='right',
        #         font=dict(
        #             size=font_size,
        #             color='rgba(0,0,0,0)'
        #         )
        #     )
        # )
    
    fig.add_trace(heatmap, row=idex+1, col=1)
    
    dtick = min(100, len(current_x))
    slice_step = min(100, len(current_x))

    fig.update_xaxes(
        row=idex+1, 
        col=1,
        dtick=dtick,
        tickfont=dict(size=font_size),
        tickvals=x[int(start):int(end):slice_step],
        title_font=dict(
            size=font_size,  
            color='black',
        ),
    )

    fig.update_yaxes(
        nticks=10,
        tickvals=list(range(0, len(y), 10)),  
        ticktext=y[::10],  #
        title_text='分卷: No.{}'.format(i+1), 
        row=idex+1, 
        col=1,
        automargin=True,
        tickfont=dict(size=font_size),
        title_font=dict(
            size=font_size,  
            color='black',
        ),
    )

    # # Set the gap between each unit
    # fig.data[idex].xgap = 1  
    # fig.data[idex].ygap = 1  


    heatmap_height_total += heatmap_height 
    idex +=1
    
    print('heatmap_height', heatmap_height)
    print('heatmap_height_total', heatmap_height_total)
    
    if heatmap_height_total > a4_height_pixels  or i == rows-1:
        re_fig = deepcopy(fig)
        if png_idx == 1:
            re_fig.update_layout(
                autosize=True,
                showlegend=False,
                width=a4_width_pixels,
                height=a4_height_pixels,
                # margin=dict(
                #     l=50,
                #     r=50,
                #     b=50,
                #     t=100,
                #     pad=10
                # ),
                font=font,
                title={
                    'text': '薄膜地形图',
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': dict(
                        size=title_font_size,
                        color='red'
                    )
                },
                annotations=[
                    dict(
                        x=0.2,  
                        y=1.1,  
                        xref='paper',
                        yref='paper',
                        text='卷信息: '+ str(x[-1]) + '毫米',  
                        showarrow=False,
                        font=dict(
                            size=title_font_size,  
                            color='Blue',
                        ),
                    ),
                    dict(
                        x=0.8, 
                        y=1.1,  
                        xref='paper',
                        yref='paper',
                        text='日期: ' + str(datetime.datetime.today()),  
                        showarrow=False,
                        font=dict(
                            size=title_font_size,  
                            color='Blue',
                        )
                    )
                ]
            )
        else :
            re_fig.update_layout(
                autosize=False,
                showlegend=False,
                width=a4_width_pixels,
                height=a4_height_pixels,
                font=font,
                margin=dict(
                    t= 0.2 * a4_height_pixels - title_font_size - colorbar_thickness , # minus the fontsize and thickness
                ),
            )        
   
        plot_path = os.path.join(save_dir,f"topographic_part_{png_idx}.png")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        re_fig.write_image(plot_path,width=a4_width_pixels,height=a4_height_pixels) 
        image_paths.append(plot_path)
        print(f'Saved {plot_path}')                   
        
        fig = make_subplots(rows=create_subplots, cols=1) if i != rows - 1 else None
        heatmap_height_total = 0    
        idex = 0
        png_idx +=1
           
            
images = [Image.open(x) for x in image_paths]
widths, heights = zip(*(i.size for i in images))


total_width = max(widths)
max_height = sum(heights)

new_img = Image.new('RGB', (total_width, max_height))

y_offset = 0
for img in images:
    new_img.paste(img, (0, y_offset))
    y_offset += img.height

new_img.save(os.path.join(save_dir, 'topographic_map.png'),encoding='utf-8')
