import json
from datetime import datetime, timedelta
from models import db, AlumnoEvento

def track_event(id_alumno, tipo_evento, metadata_dict=None):
    """
    Persists a user event to the database.
    """
    metadata_json = None
    if metadata_dict:
        try:
            metadata_json = json.dumps(metadata_dict)
        except Exception as e:
            print(f"Error encoding metadata for event: {e}")
            
    try:
        evento = AlumnoEvento(
            id_alumno=id_alumno,
            tipo_evento=tipo_evento,
            metadata_json=metadata_json,
            fecha_evento=datetime.utcnow()
        )
        db.session.add(evento)
        db.session.commit()
        
        # Check for repetitive tutoring cancellations (3 or more in last 30 days)
        if tipo_evento == 'cancelar_tutoria':
            try:
                from models import Alumno, AuditoriaActividad
                alumno = Alumno.query.get(id_alumno)
                if alumno:
                    one_month_ago = datetime.utcnow() - timedelta(days=30)
                    cancel_count = AlumnoEvento.query.filter_by(id_alumno=id_alumno, tipo_evento='cancelar_tutoria')\
                        .filter(AlumnoEvento.fecha_evento >= one_month_ago).count()
                    
                    if cancel_count >= 3:
                        # Log alert in AuditoriaActividad for the tutoring admin
                        alerta_existente = AuditoriaActividad.query.filter_by(
                            id_usuario=alumno.id_usuario,
                            accion="ALERTA: Cancelaciones Repetitivas"
                        ).order_by(AuditoriaActividad.fecha.desc()).first()
                        
                        # Only log a new alert if the last one was more than 1 day ago to prevent duplicate flood
                        should_log = True
                        if alerta_existente:
                            diff = datetime.utcnow() - alerta_existente.fecha
                            if diff.total_seconds() < 86400: # 24 hours
                                should_log = False
                                
                        if should_log:
                            alerta = AuditoriaActividad(
                                id_usuario=alumno.id_usuario,
                                username=alumno.usuario.username if alumno.usuario else id_alumno,
                                rol="Estudiante",
                                accion="ALERTA: Cancelaciones Repetitivas",
                                detalles=f"El estudiante {alumno.nombre} (ID: {id_alumno}) ha cancelado {cancel_count} tutorías en los últimos 30 días.",
                                fecha=datetime.utcnow()
                            )
                            db.session.add(alerta)
                            db.session.commit()
            except Exception as ex:
                print(f"Error checking repetitive cancellations: {ex}")
                
        return evento
    except Exception as e:
        db.session.rollback()
        print(f"Error tracking event in database: {e}")
        return None

def get_recent_events(id_alumno, limit=5):
    """
    Returns the latest N events for a student.
    """
    try:
        events = AlumnoEvento.query.filter_by(id_alumno=id_alumno)\
            .order_by(AlumnoEvento.fecha_evento.desc())\
            .limit(limit).all()
        res = []
        for e in events:
            meta = {}
            if e.metadata_json:
                try:
                    meta = json.loads(e.metadata_json)
                except Exception:
                    pass
            res.append({
                "id_evento": e.id_evento,
                "tipo_evento": e.tipo_evento,
                "metadata": meta,
                "fecha_evento": e.fecha_evento.isoformat()
            })
        return res
    except Exception as e:
        print(f"Error fetching recent events: {e}")
        return []

def get_engagement_signals(id_alumno):
    """
    Calculates behavioral engagement signals for a student.
    """
    signals = {
        "tutorias_canceladas_ultimo_mes": 0,
        "dias_sin_abrir_pizarra": 0,
        "racha_dias_activos": 0,
        "ultima_busqueda_libro": None
    }
    
    try:
        now = datetime.utcnow()
        one_month_ago = now - timedelta(days=30)
        
        # 1. tutorias_canceladas_ultimo_mes
        cancel_events = AlumnoEvento.query.filter_by(id_alumno=id_alumno, tipo_evento='cancelar_tutoria')\
            .filter(AlumnoEvento.fecha_evento >= one_month_ago).count()
        signals["tutorias_canceladas_ultimo_mes"] = cancel_events
        
        # 2. dias_sin_abrir_pizarra
        pizarra_events = AlumnoEvento.query.filter_by(id_alumno=id_alumno)\
            .filter(AlumnoEvento.tipo_evento.in_(['subida_pizarra', 'nota_pizarra']))\
            .order_by(AlumnoEvento.fecha_evento.desc()).first()
            
        if pizarra_events:
            diff = now - pizarra_events.fecha_evento
            signals["dias_sin_abrir_pizarra"] = diff.days
        else:
            # Default fallback when no pizarra activity has been logged yet
            signals["dias_sin_abrir_pizarra"] = 30 # Default to 30 days inactive
            
        # 3. racha_dias_activos (last 7 days active count)
        seven_days_ago = now - timedelta(days=7)
        recent_events = AlumnoEvento.query.filter_by(id_alumno=id_alumno)\
            .filter(AlumnoEvento.fecha_evento >= seven_days_ago).all()
            
        active_days = set()
        for e in recent_events:
            active_days.add(e.fecha_evento.date())
            
        signals["racha_dias_activos"] = len(active_days)
        
        # 4. ultima_busqueda_libro
        last_search = AlumnoEvento.query.filter_by(id_alumno=id_alumno, tipo_evento='busqueda_libro')\
            .order_by(AlumnoEvento.fecha_evento.desc()).first()
            
        if last_search and last_search.metadata_json:
            try:
                meta = json.loads(last_search.metadata_json)
                signals["ultima_busqueda_libro"] = meta.get("query") or meta.get("titulo") or meta.get("tema")
            except Exception:
                pass
                
    except Exception as e:
        print(f"Error calculating engagement signals: {e}")
        
    return signals
