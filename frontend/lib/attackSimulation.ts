export interface AttackStep {
  id: number;
  label: string;
  description: string;
  icon: string;           // emoji icon for the step
  payload: {
    entity_type: 'CUSTOMER_SESSION' | 'EMPLOYEE_ACCESS';
    entity_id: string;
    event_data: {
      sim_swap_flag: boolean;
      is_new_device: boolean;
      geovelocity_jump_km: number;
      is_first_time_beneficiary: boolean;
      outside_hours: boolean;
      accounts_accessed_count: number;
    };
  };
  expectedScore: number;  // for UI hint only
}

export const ATTACK_STEPS: AttackStep[] = [
  {
    id: 1,
    label: "Device Login",
    description: "Attacker logs in from a new unrecognized device.",
    icon: "📱",
    payload: {
      entity_type: "CUSTOMER_SESSION",
      entity_id: "CUST_ATK_SIM_001",
      event_data: {
        sim_swap_flag: false,
        is_new_device: true,
        geovelocity_jump_km: 0,
        is_first_time_beneficiary: false,
        outside_hours: false,
        accounts_accessed_count: 0
      }
    },
    expectedScore: 12
  },
  {
    id: 2,
    label: "SIM Swap Detected",
    description: "Telecom provider flags a SIM swap on this number.",
    icon: "🔄",
    payload: {
      entity_type: "CUSTOMER_SESSION",
      entity_id: "CUST_ATK_SIM_001",
      event_data: {
        sim_swap_flag: true,
        is_new_device: true,
        geovelocity_jump_km: 0,
        is_first_time_beneficiary: false,
        outside_hours: false,
        accounts_accessed_count: 0
      }
    },
    expectedScore: 38
  },
  {
    id: 3,
    label: "Geovelocity Jump",
    description: "Login from Mumbai detected — last session was in Delhi 45 min ago (1,247 km).",
    icon: "📍",
    payload: {
      entity_type: "CUSTOMER_SESSION",
      entity_id: "CUST_ATK_SIM_001",
      event_data: {
        sim_swap_flag: true,
        is_new_device: true,
        geovelocity_jump_km: 1247,
        is_first_time_beneficiary: false,
        outside_hours: false,
        accounts_accessed_count: 0
      }
    },
    expectedScore: 61
  },
  {
    id: 4,
    label: "New Beneficiary Added",
    description: "First-time beneficiary added — unknown account at external bank.",
    icon: "👤",
    payload: {
      entity_type: "CUSTOMER_SESSION",
      entity_id: "CUST_ATK_SIM_001",
      event_data: {
        sim_swap_flag: true,
        is_new_device: true,
        geovelocity_jump_km: 1247,
        is_first_time_beneficiary: true,
        outside_hours: false,
        accounts_accessed_count: 0
      }
    },
    expectedScore: 79
  },
  {
    id: 5,
    label: "Transfer ₹75,000 Attempted",
    description: "High-value transfer to new beneficiary initiated immediately after adding.",
    icon: "💸",
    payload: {
      entity_type: "CUSTOMER_SESSION",
      entity_id: "CUST_ATK_SIM_001",
      event_data: {
        sim_swap_flag: true,
        is_new_device: true,
        geovelocity_jump_km: 1247,
        is_first_time_beneficiary: true,
        outside_hours: true,
        accounts_accessed_count: 0
      }
    },
    expectedScore: 91
  }
];
