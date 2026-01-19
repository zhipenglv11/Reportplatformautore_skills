import React, { useState, useEffect } from 'react';
import { Loader2, Sparkles, CheckCircle, AlertCircle } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Button } from './ui/button';

interface Skill {
  name: string;
  type: 'imperative' | 'declarative';
  display_name?: string;
  description?: string;
  version?: string;
  has_script?: boolean;
  group?: string;
}

interface SkillsList {
  imperative: string[];
  declarative: string[];
}

interface SkillSelectorProps {
  onSkillSelect?: (skillName: string, skillType: 'imperative' | 'declarative') => void;
  selectedSkill?: string;
  showOnlyDeclarative?: boolean;
  groupFilter?: string;
  className?: string;
}

export default function SkillSelector({
  onSkillSelect,
  selectedSkill,
  showOnlyDeclarative = true,
  groupFilter,
  className = '',
}: SkillSelectorProps) {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '';
  const buildApiUrl = (path: string) => {
    if (!apiBase) {
      return path;
    }
    const normalizedBase = apiBase.replace(/\/$/, '');
    return `${normalizedBase}${path.startsWith('/') ? path : `/${path}`}`;
  };

  const [skills, setSkills] = useState<SkillsList>({ imperative: [], declarative: [] });
  const [skillDetails, setSkillDetails] = useState<Record<string, Skill>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 加载技能列表
  useEffect(() => {
    const loadSkills = async () => {
      try {
        setLoading(true);
        const response = await fetch(buildApiUrl('/api/skills/list'));
        if (!response.ok) {
          const errorText = await response.text().catch(() => response.statusText);
          let message = errorText;
          try {
            const parsed = JSON.parse(errorText);
            message = parsed.detail || parsed.message || errorText;
          } catch (_) {
            if (!message) {
              message = response.statusText;
            }
          }
          throw new Error(message || `Failed to load skills (${response.status})`);
        }
        const data: SkillsList = await response.json();
        setSkills(data);

        // 加载声明式技能的详细信息
        if (data.declarative.length > 0) {
          const detailsPromises = data.declarative.map(async (skillName) => {
            try {
              const detailResponse = await fetch(
                buildApiUrl(`/api/skill/${encodeURIComponent(skillName)}/info`)
              );
              if (detailResponse.ok) {
                const detail = await detailResponse.json();
                return { name: skillName, detail };
              }
            } catch (e) {
              console.error(`Failed to load skill info for ${skillName}:`, e);
            }
            return null;
          });

          const details = await Promise.all(detailsPromises);
          const detailsMap: Record<string, Skill> = {};
          details.forEach((item) => {
            if (item) {
              detailsMap[item.name] = item.detail;
            }
          });
          setSkillDetails(detailsMap);
        }
      } catch (err: any) {
        const message = err?.message || 'Failed to load skills';
        setError(message === 'Failed to fetch' ? '无法连接技能服务，请确认后端已启动或代理配置正确' : message);
        console.error('Error loading skills:', err);
      } finally {
        setLoading(false);
      }
    };

    loadSkills();
  }, []);

  const availableSkills = showOnlyDeclarative ? skills.declarative : [...skills.imperative, ...skills.declarative];
  const filteredSkills = groupFilter
    ? availableSkills.filter((skillName) => skillDetails[skillName]?.group === groupFilter)
    : availableSkills;

  const handleSkillChange = (skillName: string) => {
    const skillType = skills.declarative.includes(skillName) ? 'declarative' : 'imperative';
    onSkillSelect?.(skillName, skillType);
  };

  if (loading) {
    return (
      <div className={`flex items-center gap-2 text-slate-500 ${className}`}>
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">加载技能中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center gap-2 text-red-500 ${className}`}>
        <AlertCircle className="w-4 h-4" />
        <span className="text-sm">加载失败: {error}</span>
      </div>
    );
  }

  if (filteredSkills.length === 0) {
    return (
      <div className={`text-slate-500 text-sm ${className}`}>
        暂无可用技能
      </div>
    );
  }

  return (
    <div className={className}>
      <Select value={selectedSkill || ''} onValueChange={handleSkillChange}>
        <SelectTrigger className="w-full">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-500" />
            <SelectValue placeholder="选择技能..." />
          </div>
        </SelectTrigger>
        <SelectContent>
          {filteredSkills.map((skillName) => {
            const detail = skillDetails[skillName];
            const isDeclarative = skills.declarative.includes(skillName);
            return (
              <SelectItem key={skillName} value={skillName}>
                <div className="flex flex-col max-w-[320px]">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{detail?.display_name || skillName}</span>
                    {isDeclarative && (
                      <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                        声明式
                      </span>
                    )}
                  </div>
                  {/* description shown in the selected-skill panel below */}
                </div>
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
      
      {selectedSkill && skillDetails[selectedSkill] && (
        <div className="mt-2 p-2 bg-slate-50 rounded-lg text-xs text-slate-600">
          <div className="font-medium mb-1">
            {skillDetails[selectedSkill].display_name || selectedSkill}
          </div>
          <div className="text-slate-500">{skillDetails[selectedSkill].description}</div>
          {skillDetails[selectedSkill].version && (
            <div>版本: {skillDetails[selectedSkill].version}</div>
          )}
        </div>
      )}
    </div>
  );
}
