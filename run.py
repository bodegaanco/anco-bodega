from app import create_app, db
from app.models import Usuario, Producto

app = create_app()

def seed():
    """Carga datos iniciales: usuarios y productos reales de ANCO"""
    with app.app_context():
        db.create_all()

        # Crear usuarios si no existen
        if not Usuario.query.filter_by(email='bodega.anco@gmail.com').first():
            bodeguero = Usuario(
                nombre='Bodeguero ANCO',
                email='bodega.anco@gmail.com',
                rol='bodeguero'
            )
            bodeguero.set_password('anco2025')
            db.session.add(bodeguero)
            print('✅ Usuario bodeguero creado')

        if not Usuario.query.filter_by(email='franciscomunozg2002@gmail.com').first():
            supervisor = Usuario(
                nombre='Francisco Muñoz',
                email='franciscomunozg2002@gmail.com',
                rol='supervisor'
            )
            supervisor.set_password('anco2025')
            db.session.add(supervisor)
            print('✅ Usuario supervisor creado')

        # Productos reales de ANCO desde Excel
        productos_anco = [
            ('34000712', 'ABRAZADERA,ASB-CEM,DN75MM,(90-105)L200MM', 'C/U', 'Abrazaderas'),
            ('30000070', 'GOLILLA,VAINA,P/MEDIDOR,13MM', 'C/U', 'Medidores'),
            ('30000072', 'TUERCA,ENTRADA,15MM', 'C/U', 'Medidores'),
            ('30000077', 'TUERCA,SALIDA,ROSCA,7/8,MEDIDOR,13MM', 'C/U', 'Medidores'),
            ('30000080', 'VAINA,HILADA,MEDIDOR,13MM', 'C/U', 'Medidores'),
            ('34000404', 'UNION,UNIV,DN 200MM,RANG(222-250)MM', 'C/U', 'Uniones'),
            ('34000494', 'CODO REDUCCION,BRONCE,SS,DN 38x32MM', 'C/U', 'Codos'),
            ('34000678', 'CAÑERIA,PVC COLECTOR,CLASE T2,DN 180 MM', 'M', 'Cañerías'),
            ('34000717', 'ABRAZADERA,REPAR,RANG(119-130),L-300MM', 'C/U', 'Abrazaderas'),
            ('34000726', 'ABRAZADERA,REPAR,RANG(88-98),L-300MM', 'C/U', 'Abrazaderas'),
            ('34000728', 'ABRAZADERA,REPAR,RANG(95-105),L-300MM', 'C/U', 'Abrazaderas'),
            ('34000742', 'ADAPTADOR,PVC,ANGER-GIB,(110X100)MM', 'C/U', 'Adaptadores'),
            ('34000743', 'ADAPTADOR,PVC,ANGER-GIB,(125X125)MM', 'C/U', 'Adaptadores'),
            ('34000744', 'ADAPTADOR,PVC,ANGER-GIB,(140X125)MM', 'C/U', 'Adaptadores'),
            ('34000745', 'ADAPTADOR,PVC,ANGER-GIB,(160X150)MM', 'C/U', 'Adaptadores'),
            ('34000746', 'ADAPTADOR,PVC,ANGER-GIB,(200X200)MM', 'C/U', 'Adaptadores'),
            ('34000751', 'ADAPTADOR,PVC,ANGER-GIB,(75X75)MM', 'C/U', 'Adaptadores'),
            ('34000752', 'ADAPTADOR,PVC,ANGER-GIB,(90X75)MM', 'C/U', 'Adaptadores'),
            ('34000788', 'COLLAR TOMA EN CARGA METALICO 3/4"', 'C/U', 'Collares'),
            ('34000789', 'CAÑERIA,COBRE,TIPO L,DN 13MM', 'M', 'Cañerías'),
            ('34000790', 'CAÑERIA,COBRE,TIPO L,DN 19MM', 'M', 'Cañerías'),
            ('34000791', 'CAÑERIA,COBRE,TIPO L,DN 25MM', 'M', 'Cañerías'),
            ('34000792', 'CAÑERIA,COBRE,TIPO L,DN 32MM', 'M', 'Cañerías'),
            ('34000793', 'CAÑERIA,COBRE,TIPO L,DN 38MM', 'M', 'Cañerías'),
            ('34000794', 'CAÑERIA,COBRE,TIPO L,DN 50MM', 'M', 'Cañerías'),
            ('34000799', 'CAÑERIA,HDPE,PE 100,PN 10,DN 32MM', 'M', 'Cañerías'),
            ('34000803', 'CAÑERIA,HDPE,PE 100,PN 10,DN 25MM,COEXT', 'M', 'Cañerías'),
            ('34000806', 'CAÑERIA,PVC,CLASE 10,DN 110 MM', 'M', 'Cañerías'),
            ('34000807', 'CAÑERIA,PVC,CLASE 10,DN 125 MM', 'M', 'Cañerías'),
            ('34000808', 'CAÑERIA,PVC,CLASE 10,DN 140 MM', 'M', 'Cañerías'),
            ('34000809', 'CAÑERIA,PVC,CLASE 10,DN 160 MM', 'M', 'Cañerías'),
            ('34000811', 'CAÑERIA,PVC,CLASE 10,DN 200 MM', 'M', 'Cañerías'),
            ('34000820', 'CAÑERIA,PVC,CLASE 10,DN 63 MM', 'M', 'Cañerías'),
            ('34000821', 'CAÑERIA,PVC,CLASE 10,DN 75 MM', 'M', 'Cañerías'),
            ('34000822', 'CAÑERIA,PVC,CLASE 10,DN 90 MM', 'M', 'Cañerías'),
            ('34000825', 'CINCHA,ACERO,INOX,DN-100,(110-130)MM', 'C/U', 'Cinchas'),
            ('34000826', 'CINCHA,ACERO,INOX,DN-125,(130-150)MM', 'C/U', 'Cinchas'),
            ('34000827', 'CINCHA,ACERO,INOX,DN-150,(160-180)MM', 'C/U', 'Cinchas'),
            ('34000834', 'CINCHA,ACERO,INOX,DN-60,(70-90)MM', 'C/U', 'Cinchas'),
            ('34000835', 'CINCHA,ACERO,INOX,DN-80,(90-110)MM', 'C/U', 'Cinchas'),
            ('34000837', 'CODO 90°,HDPE,32X1PULG,PHILMAC97774300', 'C/U', 'Codos'),
            ('34000840', 'CODO REDUCCION,BRONCE,SS,DN 19x13MM', 'C/U', 'Codos'),
            ('34000844', 'CODO,BRONCE,HE-S,DN 13MM', 'C/U', 'Codos'),
            ('34000845', 'CODO,BRONCE,HE-S,DN 19MM', 'C/U', 'Codos'),
            ('34000846', 'CODO,BRONCE,HE-S,DN 25MM', 'C/U', 'Codos'),
            ('34000848', 'CODO,BRONCE,HE-S,DN 38MM', 'C/U', 'Codos'),
            ('34000850', 'CODO,BRONCE,HI-HE,DN 13MM', 'C/U', 'Codos'),
            ('34000851', 'CODO,BRONCE,HI-HE,DN 19MM', 'C/U', 'Codos'),
            ('34000852', 'CODO,BRONCE,HI-HE,DN 25MM', 'C/U', 'Codos'),
            ('34000854', 'CODO,BRONCE,HI-HE,DN 38MM', 'C/U', 'Codos'),
            ('34000862', 'CODO,BRONCE,HI-S,DN 13MM', 'C/U', 'Codos'),
            ('34000863', 'CODO,BRONCE,HI-S,DN 19MM', 'C/U', 'Codos'),
            ('34000864', 'CODO,BRONCE,HI-S,DN 25MM', 'C/U', 'Codos'),
            ('34000865', 'CODO,BRONCE,HI-S,DN 32MM', 'C/U', 'Codos'),
            ('34000866', 'CODO,BRONCE,HI-S,DN 38MM', 'C/U', 'Codos'),
            ('34000868', 'CODO,BRONCE,SS,DN 13MM', 'C/U', 'Codos'),
            ('34000869', 'CODO,BRONCE,SS,DN 19MM', 'C/U', 'Codos'),
            ('34000870', 'CODO,BRONCE,SS,DN 25MM', 'C/U', 'Codos'),
            ('34000871', 'CODO,BRONCE,SS,DN 32MM', 'C/U', 'Codos'),
            ('34000872', 'CODO,BRONCE,SS,DN 38MM', 'C/U', 'Codos'),
            ('34000873', 'CODO,BRONCE,SS,DN 50MM', 'C/U', 'Codos'),
            ('34000918', 'COPLA,BRONCE,SS,DN 13MM', 'C/U', 'Coplas'),
            ('34000919', 'COPLA,BRONCE,SS,DN 19MM', 'C/U', 'Coplas'),
            ('34000920', 'COPLA,BRONCE,SS,DN 25MM', 'C/U', 'Coplas'),
            ('34000921', 'COPLA,BRONCE,SS,DN 32MM', 'C/U', 'Coplas'),
            ('34000922', 'COPLA,BRONCE,SS,DN 38MM', 'C/U', 'Coplas'),
            ('34000923', 'COPLA,BRONCE,SS,DN 50MM', 'C/U', 'Coplas'),
            ('34000929', 'COPLA,PVC,REPARACION,ANGER,110MM', 'C/U', 'Coplas'),
            ('34000930', 'COPLA,PVC,REPARACION,ANGER,125MM', 'C/U', 'Coplas'),
            ('34000931', 'COPLA,PVC,REPARACION,ANGER,140MM', 'C/U', 'Coplas'),
            ('34000932', 'COPLA,PVC,REPARACION,ANGER,160MM', 'C/U', 'Coplas'),
            ('34000933', 'COPLA,PVC,REPARACION,ANGER,200MM', 'C/U', 'Coplas'),
            ('34000937', 'COPLA,PVC,REPARACION,ANGER,63MM', 'C/U', 'Coplas'),
            ('34000938', 'COPLA,PVC,REPARACION,ANGER,75MM', 'C/U', 'Coplas'),
            ('34000939', 'COPLA,PVC,REPARACION,ANGER,90MM', 'C/U', 'Coplas'),
            ('34000940', 'COPLA,REDUCCION,BRONCE,SS,(19X13)MM', 'C/U', 'Coplas'),
            ('34000941', 'COPLA,REDUCCION,BRONCE,SS,(25X19)MM', 'C/U', 'Coplas'),
            ('34000944', 'COPLA,REDUCCION,BRONCE,SS,(38X25)MM', 'C/U', 'Coplas'),
            ('34000947', 'COPLA,TRANS,HDPE,PEXCOBRE,25MMX3/4PULG', 'C/U', 'Coplas'),
            ('34000948', 'COPLA,TRANS,HDPE,PEXCOBRE,32MMX1PULG', 'C/U', 'Coplas'),
            ('34000969', 'CURVA,PVC,ANGER-ESPIGA,(1/4X110)MM', 'C/U', 'Curvas'),
            ('34000975', 'CURVA,PVC,ANGER-ESPIGA,(1/8X110)MM', 'C/U', 'Curvas'),
            ('34001013', 'GUARDA LLAVE,FE FDO, P/VALVULA', 'C/U', 'Llaves'),
            ('34001019', 'LLAVE,COLLAR,BRONCE,HE-HE,DN 19MM', 'C/U', 'Llaves'),
            ('34001020', 'LLAVE,COLLAR,BRONCE,HE-HE,DN 25MM', 'C/U', 'Llaves'),
            ('34001022', 'LLAVE,COLLAR,BRONCE,HE-HE,DN 38MM', 'C/U', 'Llaves'),
            ('34001024', 'LLAVE,PASO BOLA,BRONCE,HI-HI,DN 13MM', 'C/U', 'Llaves'),
            ('34001025', 'LLAVE,PASO BOLA,BRONCE,HI-HI,DN 19MM', 'C/U', 'Llaves'),
            ('34001026', 'LLAVE,PASO BOLA,BRONCE,HI-HI,DN 25MM', 'C/U', 'Llaves'),
            ('34001031', 'LLAVE,PASO,BRONCE,SS,DN 13MM', 'C/U', 'Llaves'),
            ('34001032', 'LLAVE,PASO,BRONCE,SS,DN 19MM', 'C/U', 'Llaves'),
            ('34001056', 'REDUCCION,PVC,ANGER-ESPIGA,(110X90)MM', 'C/U', 'Reducciones'),
            ('34001124', 'TAPON,PVC,ANGER,110MM', 'C/U', 'Tapones'),
            ('34001125', 'TAPON,PVC,ANGER,125MM', 'C/U', 'Tapones'),
            ('34001129', 'TAPON,PVC,ANGER,90MM', 'C/U', 'Tapones'),
            ('34001131', 'TEE,BRONCE,SSS,(13X13)MM', 'C/U', 'Tees'),
            ('34001133', 'TEE,BRONCE,SSS,(19X19)MM', 'C/U', 'Tees'),
            ('34001165', 'TERMINAL,BRONCE,HE-S,13MM', 'C/U', 'Terminales'),
            ('34001166', 'TERMINAL,BRONCE,HE-S,19MM', 'C/U', 'Terminales'),
            ('34001167', 'TERMINAL,BRONCE,HE-S,25MM', 'C/U', 'Terminales'),
            ('34001168', 'TERMINAL,BRONCE,HE-S,32MM', 'C/U', 'Terminales'),
            ('34001169', 'TERMINAL,BRONCE,HE-S,38MM', 'C/U', 'Terminales'),
            ('34001170', 'TERMINAL,BRONCE,HE-S,50MM', 'C/U', 'Terminales'),
            ('34001172', 'TERMINAL,BRONCE,HI-S,13MM', 'C/U', 'Terminales'),
            ('34001173', 'TERMINAL,BRONCE,HI-S,19MM', 'C/U', 'Terminales'),
            ('34001174', 'TERMINAL,BRONCE,HI-S,25MM', 'C/U', 'Terminales'),
            ('34001175', 'TERMINAL,BRONCE,HI-S,32MM', 'C/U', 'Terminales'),
            ('34001176', 'TERMINAL,BRONCE,HI-S,38MM', 'C/U', 'Terminales'),
            ('34001177', 'TERMINAL,BRONCE,HI-S,50MM', 'C/U', 'Terminales'),
            ('34001190', 'TERMINAL,HDPE-CU,(25X3/4)', 'C/U', 'Terminales'),
            ('34001195', 'TERMINAL,PVC,CEMENTAR-HE,(20X1/2)', 'C/U', 'Terminales'),
            ('34001196', 'TERMINAL,PVC,CEMENTAR-HE,(25X3/4)', 'C/U', 'Terminales'),
            ('34001200', 'TERMINAL,PVC,CEMENTAR-HI,(20X1/2)', 'C/U', 'Terminales'),
            ('34001201', 'TERMINAL,PVC,CEMENTAR-HI,(25X3/4)', 'C/U', 'Terminales'),
            ('34001202', 'TERMINAL,PVC,CEMENTAR-HI,(32X1)', 'C/U', 'Terminales'),
            ('34001221', 'UNION,AMERICANA,BRONCE,SS,13MM', 'C/U', 'Uniones'),
            ('34001222', 'UNION,AMERICANA,BRONCE,SS,19MM', 'C/U', 'Uniones'),
            ('34001223', 'UNION,AMERICANA,BRONCE,SS,25MM', 'C/U', 'Uniones'),
            ('34001224', 'UNION,AMERICANA,BRONCE,SS,32MM', 'C/U', 'Uniones'),
            ('34001225', 'UNION,AMERICANA,BRONCE,SS,38MM', 'C/U', 'Uniones'),
            ('34001226', 'UNION,AMERICANA,BRONCE,SS,50MM', 'C/U', 'Uniones'),
            ('34001251', 'UNION,UNIV,DN 125MM,RANG(132-154)MM', 'C/U', 'Uniones'),
            ('34001253', 'UNION,UNIV,DN 150MM,RANG(159-182)MM', 'C/U', 'Uniones'),
            ('34001258', 'UNION,UNIV,DN 75MM,RANG(84-108)MM', 'C/U', 'Uniones'),
            ('34001259', 'UNION,UNIV,DN,100MM,RANG(108-130)MM', 'C/U', 'Uniones'),
            ('34001274', 'ANILLO,FE FDO,TAPA CAM,CALZADA,(70X10)CM', 'C/U', 'Cámaras'),
            ('34001279', 'CAÑERIA,PVC COLECTOR,CLASE II,DN 200 MM', 'M', 'Cañerías'),
            ('34001286', 'CAÑERIA,PVC,SANITARIO,DN 110 MM', 'M', 'Cañerías'),
            ('34001291', 'MARCO,CUADRADO,REFORZADO,GRAU(60X60)CM', 'C/U', 'Cámaras'),
            ('34001294', 'REJILLA,CIRCULAR,TAPA CAM CALZ,(69X10)CM', 'C/U', 'Cámaras'),
            ('34001295', 'TAPA CAM CUADRADA,REFORZADA,(60X60)CM', 'C/U', 'Cámaras'),
            ('34001300', 'VALVULA,ANTIRETORNO,UD,COLECTOR,DN 110MM', 'C/U', 'Válvulas'),
            ('34001541', 'CAÑERIA,HDPE,PE 80,PN 6,DN 50 MM', 'M', 'Cañerías'),
            ('34001684', 'COLLAR,TOMA EN CARGA,NYLON 6.6,3/4PULG', 'C/U', 'Collares'),
            ('34001690', 'COLLAR,TOMA EN CARGA,NYLON 6.6,1PULG', 'C/U', 'Collares'),
            ('34001694', 'LLAVE,PASO BOLA,ALUMINIO,DN 32MM,C/MANIL', 'C/U', 'Llaves'),
            ('34001695', 'LLAVE,PASO BOLA,ALUMINIO,DN 38MM,C/MANIL', 'C/U', 'Llaves'),
            ('34001696', 'LLAVE,PASO BOLA,ALUMINIO,DN 50MM,C/MANIL', 'C/U', 'Llaves'),
        ]

        cargados = 0
        for codigo, desc, unidad, categoria in productos_anco:
            if not Producto.query.filter_by(codigo=codigo).first():
                p = Producto(codigo=codigo, descripcion=desc, unidad=unidad, categoria=categoria)
                db.session.add(p)
                cargados += 1

        db.session.commit()
        print(f'✅ {cargados} productos cargados en la base de datos')
        print('🚀 Base de datos lista!')


if __name__ == '__main__':
    seed()
    app.run(debug=True)

# Para Railway/producción — crea tablas y carga datos al iniciar
with app.app_context():
    db.create_all()
    seed()
