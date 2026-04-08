import fs from 'fs';
import path from 'path';

export interface TrustProfile {
  initial_score: number;
  decay_rate: number;
  params: boolean[];
}

export interface Duty {
  role: string;
  conflict_with: string[];
}

export interface Autonomy {
  level: number;
  requires_approval_for: string[];
}

export interface AgentManifest {
  name: string;
  version: string;
  description: string;
  capabilities: string[];
  trust_profile: TrustProfile;
  equipment: string[];
  skills: string[];
  rules: string[];
  duties: Duty[];
  compliance: string[];
  autonomy: Autonomy;
}

export function parseManifest(json: string): AgentManifest {
  const raw = JSON.parse(json);
  const manifest: AgentManifest = {
    name: String(raw.name),
    version: String(raw.version),
    description: String(raw.description),
    capabilities: Array.isArray(raw.capabilities) ? raw.capabilities.map(String) : [],
    trust_profile: {
      initial_score: Number(raw.trust_profile?.initial_score) || 0.5,
      decay_rate: Number(raw.trust_profile?.decay_rate) || 25,
      params: Array.isArray(raw.trust_profile?.params) 
        ? raw.trust_profile.params.map((p: any) => Boolean(p)) 
        : Array(12).fill(false)
    },
    equipment: Array.isArray(raw.equipment) ? raw.equipment.map(String) : [],
    skills: Array.isArray(raw.skills) ? raw.skills.map(String) : [],
    rules: Array.isArray(raw.rules) ? raw.rules.map(String) : [],
    duties: Array.isArray(raw.duties) 
      ? raw.duties.map((d: any) => ({
          role: String(d.role || ''),
          conflict_with: Array.isArray(d.conflict_with) ? d.conflict_with.map(String) : []
        }))
      : [],
    compliance: Array.isArray(raw.compliance) ? raw.compliance.map(String) : [],
    autonomy: {
      level: Number(raw.autonomy?.level) || 0,
      requires_approval_for: Array.isArray(raw.autonomy?.requires_approval_for) 
        ? raw.autonomy.requires_approval_for.map(String) 
        : []
    }
  };
  return manifest;
}

export function validateManifest(manifest: AgentManifest): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!manifest.name.trim()) errors.push('Name is required');
  if (!/^\d+\.\d+\.\d+$/.test(manifest.version)) errors.push('Version must be semver (x.y.z)');
  if (manifest.trust_profile.initial_score < 0 || manifest.trust_profile.initial_score > 1) {
    errors.push('Trust profile initial_score must be between 0 and 1');
  }
  if (manifest.trust_profile.decay_rate < 0 || manifest.trust_profile.decay_rate > 100) {
    errors.push('Trust profile decay_rate must be between 0 and 100');
  }
  if (manifest.trust_profile.params.length !== 12) {
    errors.push('Trust profile params must have exactly 12 booleans');
  }
  if (manifest.autonomy.level < 0 || manifest.autonomy.level > 10) {
    errors.push('Autonomy level must be between 0 and 10');
  }
  manifest.duties.forEach((duty, idx) => {
    if (!duty.role.trim()) errors.push(`Duty ${idx}: role is required`);
  });

  return { valid: errors.length === 0, errors };
}

export function extractSOUL(md: string): string {
  const lines = md.split('\n');
  let inSection = false;
  const collected: string[] = [];

  for (const line of lines) {
    if (line.startsWith('# PERSONALITY & VALUES')) {
      inSection = true;
      continue;
    }
    if (inSection && line.startsWith('# ') && !line.startsWith('# PERSONALITY & VALUES')) {
      break;
    }
    if (inSection) {
      collected.push(line);
    }
  }

  return collected.join('\n').trim();
}

export function getSystemPrompt(manifest: AgentManifest, soul: string): string {
  const parts: string[] = [];

  parts.push(`# AGENT: ${manifest.name} v${manifest.version}`);
  parts.push(`## Description\n${manifest.description}`);

  if (soul) {
    parts.push(`## Personality & Values\n${soul}`);
  }

  if (manifest.rules.length > 0) {
    parts.push(`## Operational Rules`);
    manifest.rules.forEach(rule => parts.push(`- ${rule}`));
  }

  if (manifest.duties.length > 0) {
    parts.push(`## Duties & Role Segregation`);
    manifest.duties.forEach(duty => {
      parts.push(`- Role: ${duty.role}`);
      if (duty.conflict_with.length > 0) {
        parts.push(`  Conflicts with: ${duty.conflict_with.join(', ')}`);
      }
    });
  }

  return parts.join('\n');
}

export function checkDuties(manifest: AgentManifest, action: string): { allowed: boolean; reason: string } {
  const lowerAction = action.toLowerCase();
  for (const duty of manifest.duties) {
    const lowerRole = duty.role.toLowerCase();
    if (lowerAction.includes(lowerRole) || lowerRole.includes(lowerAction)) {
      if (duty.conflict_with.some(conflict => lowerAction.includes(conflict.toLowerCase()))) {
        return {
          allowed: false,
          reason: `Action "${action}" conflicts with duty role "${duty.role}"`
        };
      }
    }
  }
  return { allowed: true, reason: 'No duty conflicts detected' };
}

export function loadManifestFromFile(filePath: string): AgentManifest {
  const json = fs.readFileSync(filePath, 'utf-8');
  return parseManifest(json);
}

export function loadSOULFromFile(repoRoot: string): string {
  const soulPath = path.join(repoRoot, 'SOUL.md');
  if (!fs.existsSync(soulPath)) return '';
  const md = fs.readFileSync(soulPath, 'utf-8');
  return extractSOUL(md);
}