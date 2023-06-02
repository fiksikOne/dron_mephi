from machine import Pin,I2C # возможность работать с I2C ротоколом
from neopixel import NeoPixel # работа с адресными светодиодами
from MX1508 import * # драйверы двигателя
from VL53L0X import * # работа с лазерным дальномером
from tcs34725 import * # работа с датчиком цвета
from time import sleep_ms,sleep # задержки в мс и с
import uasyncio as asio # возможность асинхронн программирования
import aioespnow # асинхронный ESP-now
import network # функции работы по wi-fi

i2c_bus = I2C(0, sda=Pin(22), scl=Pin(21)) # создание шины под датчик цвета
tcs = TCS34725(i2c_bus)
tcs.gain(4)#gain must be 1, 4, 16 or 60 (значение усиления)
tcs.integration_time(80) # время накопления данных и решения по цвету
i2c_bus1 = I2C(1, sda=Pin(17), scl=Pin(16)) # вторая шина для дальномера                            # тут нужна вторая шина потому, что у дальномера и цветодатчика одинаковые адреса, а так их можно было бы на одну шину повесить                                            
tof = VL53L0X(i2c_bus1) # объект, работающий с лазерным дальномером
color=['Red','Yellow','White','Green','Black','Cyan','Blue','Magenta'] # набор обрабатываемых цветов
#Sp=1023 # значение ШИМа от 0 до 1023
#Sp1=int(Sp*0.3) # скорость для корректировки - притормаживание опережающего колеса на 70%
Lt=60 # яркость свечения светодиодов от 0 до 255
alfa=0.8 # параметр для фильтра сглаживания дистанции
debug=1 # выводится ли отладочная информация
int_ms = 200
NUM_OF_LED = 1 # количество адресных светодиодов
np = NeoPixel(Pin(26), NUM_OF_LED) # объект, работающий со светодиодами: Объект(Номер_управляющего пина, количество светодиодов)
Lt = 60

R_W_count,W_count,col_id,col_id_l,direct,di,dist,busy,busy_col,col_sel=0,0,0,0,0,0,500,0,0,5 # инициализация глобальных переменных
R_m_pin = Pin(32, Pin.IN) # пины энкодеров для использования в прерываниях
L_m_pin = Pin(25, Pin.IN)

motor_R = MX1508(19, 18)
motor_L = MX1508(4, 2)

colors_Arr = [3,7]

Sp = 400
Sp1=int(Sp*0.3)



async def stopOnColor(COL_ID):
    if(col_id==COL_ID):
        motor_R.stop()
        motor_L.stop()
        print("stopOnColor id = ", COL_ID)
    else:
        motor_R.reverse(256)
        motor_L.reverse(256)


motor_R.reverse(Sp)
motor_L.reverse(Sp)

def R_W_int(pin): # функции счета срабатываний энкодера
    global W_count
    W_count+=1
    
def L_W_int(pin):
    global W_count
    W_count+=1
    
R_m_pin.irq(trigger=Pin.IRQ_FALLING |Pin.IRQ_RISING , handler=R_W_int) #t rigger=Pin.IRQ_FALLING | - при поступлении высокого/низкого потенциала на пин энкодера вызываем функции счета
L_m_pin.irq(trigger=Pin.IRQ_FALLING |Pin.IRQ_RISING , handler=L_W_int)

def razvorot():
    count = W_count
    print("COUNT = ", count)
    i=0
    while(((W_count-count))<30):
        i=i+1
        motor_R.forward(Sp)
        motor_L.forward(Sp)
        #print("I = ", i)
        #print("count = ", count)
    motor_R.reverse(Sp)
    motor_L.reverse(Sp)



def razvorot_on_black():
    count = W_count
    print("COUNT = ", count)
    i=0
    while((W_count-count)<20):
        i=i+1
        motor_R.forward(1023)
        motor_L.reverse(1023)
        #print("I = ", i)
        #print("count = ", count)
    motor_R.reverse(Sp)
    motor_L.reverse(Sp)


async def color_det():
    global col_id,col_id_l
    rgb=tcs.read(1)
    r,g,b=rgb[0],rgb[1],rgb[2]
    h,s,v=rgb_to_hsv(r,g,b)
    print('Color is {}. R:{} G:{} B:{} H:{:.0f} S:{:.0f} V:{:.0f}'.format(color[col_id],r,g,b,h,s,v))
    if 0<h<60:
        if(0<b<100):
            col_id_l = col_id
            col_id=0
        elif(101<b<150):
            col_id_l=col_id
            col_id=7
            
            
        #col_id_l=col_id
        #col_id=0
        print("COLOR ID = ", col_id)
    elif(0<v<20):
        col_id_l=col_id
        col_id=4
    elif 61<h<120:
        col_id_l=col_id
        col_id=1
        print("COLOR ID = ", col_id)
    elif 121<h<180:
        if v>250: ####was 100
            col_id_l=col_id
            col_id=2
            print("COLOR ID = ", col_id)
        elif v>21:
            col_id_l=col_id
            col_id=3
            print(" GREEN COLOR ID = ", col_id)
        elif 0<v<20:
            col_id_l=col_id
            col_id=4
            print("BLACK BLACK COLOR ID = ", col_id)
            #razvorot()
            #razvorot_on_black()
    elif 181<h<240:
        if 30<v<60:
            col_id_l=col_id
            col_id=6
            print("COLOR ID = ", col_id)
        elif(61<v):
            col_id_l=col_id
            col_id=5
            print("COLOR ID = ", col_id)
    elif 241<h<360:
        if(0<b<100):
            col_id=0
            col_id_l = col_id
        elif(101<b<150):
            col_id=7
            col_id_l=col_id
            
#         if(241<h<300):
#             col_id_l = col_id
#             col_id = 7
#         elif(300<h<360):
#             col_id_l = col_id
#             col_id = 0
        #col_id_l=col_id
        #col_id=7
        print("COLOR ID = ", col_id)
    if debug:
        print('Color is {}. R:{} G:{} B:{} H:{:.0f} S:{:.0f} V:{:.0f}'.format(color[col_id],r,g,b,h,s,v))
           
        
async def LED_cont(int_ms): # управление светодиодами
    if col_id==0: # диод цвета
        np[0]=(Lt,0,0)
    elif col_id==1:
        np[0]=(Lt,Lt,0)
    elif col_id==2:
        np[0]=(Lt,Lt,Lt)
    elif col_id==3:
        np[0]=(0,Lt,0)
    elif col_id==4:
        np[0]=(0,0,0)
        np.write()
        await asio.sleep_ms(100)
        np[0]=(Lt,0,0)
        np.write()
        await asio.sleep_ms(100)
        razvorot()
        razvorot_on_black()
    elif col_id==5:
        np[0]=(0,Lt,Lt)
    elif col_id==6:
        np[0]=(0,0,Lt) 
    elif col_id==7:
        np[0]=(Lt,0,Lt)
    np.write() # отправление значений на диоды

async def dist_det(): # определение расстояния
    global dist
    tof.start()
    dist_l=dist # запомнили прошлую дистанцию
    dist=tof.read()-29 # получили новую + корректировка
    tof.stop()
    dist=int(alfa*dist+(1-alfa)*dist_l) # сглаживание и получение итоговой дистанции
    if(dist<250):
        razvorot()
        razvorot_on_black()
    if debug:
        print('Distance is {}'.format(dist))
        
        
async def ping(int_ms):
    global W_count
    while 1:
        await color_det()
        await stopOnColor(0)
        await dist_det()
        await LED_cont(100)
        print('W_count is  {}'.format(W_count))
        print('\nping\n')
        await asio.sleep_ms(int_ms)
        
# define loop
loop = asio.get_event_loop()

#create looped tasks # запуск всех зацикленных сопрограмм
loop.create_task(ping(int_ms))
# loop run forever
loop.run_forever()