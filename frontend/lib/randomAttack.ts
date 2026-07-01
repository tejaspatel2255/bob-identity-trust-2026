import { Persona } from './types';

export function getRandomAttack(): Persona {
  const attackTypes = [
    {
      name: 'Sim Swap Fraud',
      desc: 'Simulated SIM swap occurrence followed by immediate transaction request.',
      entityType: 'CUSTOMER_SESSION' as const,
      entityId: `CUST_SIM_SWAP_${Math.floor(1000 + Math.random() * 9000)}`,
      trustLevel: 'danger' as const,
      eventData: () => ({
        sim_swap_flag: true,
        is_new_device: Math.random() > 0.3,
        geovelocity_jump_km: Math.floor(100 + Math.random() * 1000),
        is_first_time_beneficiary: Math.random() > 0.2,
        outside_working_hours: Math.random() > 0.5,
        behavioral_baseline_drift: parseFloat((0.6 + Math.random() * 0.35).toFixed(2)),
        typing_cadence_wpm: Math.floor(110 + Math.random() * 60),
        swipe_speed_px_per_sec: Math.floor(150 + Math.random() * 200),
      })
    },
    {
      name: 'Impossible Geovelocity',
      desc: 'Impossible travel speed/geovelocity jump between session locations.',
      entityType: 'CUSTOMER_SESSION' as const,
      entityId: `CUST_GEO_${Math.floor(1000 + Math.random() * 9000)}`,
      trustLevel: 'danger' as const,
      eventData: () => ({
        sim_swap_flag: Math.random() > 0.7,
        is_new_device: true,
        geovelocity_jump_km: Math.floor(800 + Math.random() * 3000),
        is_first_time_beneficiary: Math.random() > 0.4,
        outside_working_hours: Math.random() > 0.3,
        behavioral_baseline_drift: parseFloat((0.7 + Math.random() * 0.25).toFixed(2)),
        typing_cadence_wpm: Math.floor(120 + Math.random() * 50),
        swipe_speed_px_per_sec: Math.floor(120 + Math.random() * 150),
      })
    },
    {
      name: 'Suspicious Device Fingeprint',
      desc: 'First-time device login with high behavioral deviation profile.',
      entityType: 'CUSTOMER_SESSION' as const,
      entityId: `CUST_DEV_${Math.floor(1000 + Math.random() * 9000)}`,
      trustLevel: 'warning' as const,
      eventData: () => ({
        sim_swap_flag: false,
        is_new_device: true,
        geovelocity_jump_km: Math.floor(10 + Math.random() * 80),
        is_first_time_beneficiary: Math.random() > 0.5,
        outside_working_hours: Math.random() > 0.4,
        behavioral_baseline_drift: parseFloat((0.45 + Math.random() * 0.3).toFixed(2)),
        typing_cadence_wpm: Math.floor(80 + Math.random() * 40),
        swipe_speed_px_per_sec: Math.floor(300 + Math.random() * 200),
      })
    },
    {
      name: 'Bulk Privilege Abuse',
      desc: 'Branch employee executing bulk VIP account queries off-shift.',
      entityType: 'EMPLOYEE_ACCESS' as const,
      entityId: `EMP_ABUSE_${Math.floor(1000 + Math.random() * 9000)}`,
      trustLevel: 'purple' as const,
      eventData: () => ({
        outside_hours: Math.random() > 0.2,
        bulk_account_access: true,
        high_balance_accessed_count: Math.floor(3 + Math.random() * 8),
        recovery_requests_followed: Math.random() > 0.4,
        is_new_device: Math.random() > 0.8,
        behavioral_baseline_drift: parseFloat((0.55 + Math.random() * 0.35).toFixed(2)),
      })
    }
  ];

  const selected = attackTypes[Math.floor(Math.random() * attackTypes.length)];
  return {
    id: `persona-random-${Date.now()}`,
    name: `Random: ${selected.name}`,
    trustLevel: selected.trustLevel,
    description: selected.desc,
    entityType: selected.entityType,
    entityId: selected.entityId,
    eventData: selected.eventData()
  };
}
