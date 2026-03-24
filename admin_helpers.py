import math

def _normalize_text(value):
    return str(value or '').strip().lower()


def _suggest_reward_from_report(report, ai_analysis, waste_composition, special_equipment):
    """Estimate a fair task reward using report details + AI analysis + local market assumptions."""
    severity_multiplier = {
        'LOW': 1.0,
        'MEDIUM': 1.25,
        'HIGH': 1.55,
        'CRITICAL': 1.9,
    }

    # Local market assumptions (BDT) for urban cleanup labor/equipment.
    base_labor = 320.0
    transport_base = 90.0
    market_volatility_buffer = 0.12

    severity = (report.get('severity') or ai_analysis.get('severity') or 'MEDIUM').upper()
    severity_factor = severity_multiplier.get(severity, 1.25)

    estimated_volume = _normalize_text(ai_analysis.get('estimated_volume'))
    cleanup_time = _normalize_text(ai_analysis.get('estimated_cleanup_time'))
    env_impact = _normalize_text(ai_analysis.get('environmental_impact'))
    hazard_flag = bool(ai_analysis.get('health_hazard'))
    description = _normalize_text(report.get('description'))

    labor_cost = base_labor * severity_factor
    components = [
        {'label': 'Base labor (local daily-rate baseline)', 'amount': round(base_labor, 2)},
        {'label': f'Severity multiplier ({severity})', 'amount': round(labor_cost - base_labor, 2)},
    ]

    volume_cost = 0.0
    if any(k in estimated_volume for k in ['truck', 'large', 'multiple bags', 'bulk']):
        volume_cost = 260.0
    elif any(k in estimated_volume for k in ['medium', '1-2 bags', 'bag']):
        volume_cost = 150.0
    elif estimated_volume:
        volume_cost = 90.0
    if volume_cost:
        components.append({'label': f'Volume adjustment ({ai_analysis.get("estimated_volume")})', 'amount': volume_cost})

    time_cost = 0.0
    if any(k in cleanup_time for k in ['2-4 hour', '3-4 hour', 'half day']):
        time_cost = 220.0
    elif any(k in cleanup_time for k in ['1-2 hour', '60-120', '90 minute']):
        time_cost = 130.0
    elif cleanup_time:
        time_cost = 70.0
    if time_cost:
        components.append({'label': f'Time estimate adjustment ({ai_analysis.get("estimated_cleanup_time")})', 'amount': time_cost})

    hazard_cost = 0.0
    if hazard_flag:
        hazard_cost += 220.0
    if env_impact in ['severe', 'high']:
        hazard_cost += 130.0 if env_impact == 'high' else 220.0
    if hazard_cost:
        components.append({'label': 'Hazard/environmental risk premium', 'amount': hazard_cost})

    equipment_price_map = {
        'mask': 35,
        'glove': 25,
        'shovel': 90,
        'trolley': 180,
        'wheelbarrow': 220,
        'hazmat': 350,
        'disinfect': 120,
        'boots': 80,
        'protective': 140,
    }
    equipment_cost = 0.0
    for equipment in special_equipment:
        e = _normalize_text(equipment)
        matched = False
        for key, price in equipment_price_map.items():
            if key in e:
                equipment_cost += price
                matched = True
                break
        if not matched:
            equipment_cost += 70
    if equipment_cost:
        components.append({'label': 'Special equipment allowance', 'amount': equipment_cost})

    material_cost = 0.0
    for item in waste_composition:
        waste_type = _normalize_text(item.get('waste_type'))
        pct = float(item.get('percentage') or 0)
        if pct <= 0:
            continue
        unit = 0.0
        if any(k in waste_type for k in ['medical', 'chemical', 'hazard', 'e-waste']):
            unit = 2.0
        elif any(k in waste_type for k in ['glass', 'metal', 'construction']):
            unit = 1.2
        elif any(k in waste_type for k in ['plastic', 'mixed']):
            unit = 0.8
        else:
            unit = 0.5
        material_cost += pct * unit
    if material_cost:
        components.append({'label': 'Waste handling mix cost', 'amount': round(material_cost, 2)})

    transport_cost = transport_base
    if report.get('latitude') is not None and report.get('longitude') is not None:
        transport_cost += 25
    if any(k in description for k in ['drain', 'canal', 'roadside', 'market', 'hospital']):
        transport_cost += 35
    components.append({'label': 'Logistics/transport allowance', 'amount': round(transport_cost, 2)})

    subtotal = sum(float(c['amount']) for c in components)
    buffer = subtotal * market_volatility_buffer
    components.append({'label': 'Local market price buffer (12%)', 'amount': round(buffer, 2)})

    raw_total = subtotal + buffer
    suggested = int(math.ceil(raw_total / 50.0) * 50)
    suggested = max(300, min(3500, suggested))

    confidence_inputs = 0
    confidence_inputs += 1 if ai_analysis.get('estimated_volume') else 0
    confidence_inputs += 1 if ai_analysis.get('estimated_cleanup_time') else 0
    confidence_inputs += 1 if waste_composition else 0
    confidence_inputs += 1 if special_equipment else 0
    confidence_inputs += 1 if report.get('description') else 0
    confidence_score = min(95, 55 + confidence_inputs * 8)

    range_min = int(max(250, math.floor(suggested * 0.9 / 50.0) * 50))
    range_max = int(math.ceil(suggested * 1.1 / 50.0) * 50)

    return {
        'suggested_reward': suggested,
        'currency': 'BDT',
        'confidence': confidence_score,
        'range_min': range_min,
        'range_max': range_max,
        'severity_used': severity,
        'pricing_components': components,
        'market_basis': [
            'Urban local cleaner day-rate baseline',
            'Equipment/transport allowance from local operational assumptions',
            'Risk and volume premiums from AI analysis',
        ],
    }

