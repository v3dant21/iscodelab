'use client';
import { useId } from 'react';
import { CartLine, Dish, money } from './api';

export type Selections = Record<string, string>;
export function defaultSelections(dish: Dish): Selections {
  return Object.fromEntries((dish.customizations || []).map(group => [group.id, group.default]));
}
export function selectionKey(selections: Selections = {}) {
  return JSON.stringify(Object.entries(selections).sort(([a], [b]) => a.localeCompare(b)));
}
export function choiceLabels(dish: Dish, selections: Selections) {
  return (dish.customizations || []).map(group => `${group.label}: ${group.choices.find(choice => choice.id === (selections[group.id] || group.default))?.label || 'Choose again'}`);
}
export function lineDescription(line: Pick<CartLine, 'portion' | 'addon' | 'customization_labels'>) {
  return [line.portion, ...(line.addon ? ['Extra raita'] : []), ...(line.customization_labels || [])].join(' · ');
}
export function DishOptions({ dish, portion, addon, selections, onChange, compact = false }: {
  dish: Dish; portion: string; addon: boolean; selections: Selections; compact?: boolean;
  onChange: (portion: string, addon: boolean, selections: Selections) => void;
}) {
  const id = useId();
  return <div className={`dish-options${compact ? ' compact' : ''}`}>
    {Object.keys(dish.options).length > 1 ? <label>Portion<select aria-label={`Portion for ${dish.name}`} value={portion} onChange={e => onChange(e.target.value, addon, selections)}>{Object.entries(dish.options).map(([name, price]) => <option key={name} value={name}>{name}{price ? ` +${money(price)}` : ''}</option>)}</select></label> : <p className="serving-note">Serving: <strong>{portion}</strong> · adjust quantity for more</p>}
    {(dish.customizations || []).map(group => <fieldset key={group.id} className="preparation-group"><legend>{group.label}</legend>{compact ? <select aria-label={`${group.label} for ${dish.name}`} value={selections[group.id] || group.default} onChange={e => onChange(portion, addon, { ...selections, [group.id]: e.target.value })}>{group.choices.map(choice => <option key={choice.id} value={choice.id}>{choice.label}</option>)}</select> : <div className="preparation-choices">{group.choices.map(choice => <label key={choice.id} className={(selections[group.id] || group.default) === choice.id ? 'chosen' : ''}><input type="radio" name={`${id}-${group.id}`} value={choice.id} checked={(selections[group.id] || group.default) === choice.id} onChange={() => onChange(portion, addon, { ...selections, [group.id]: choice.id })} /><span>{choice.label}</span></label>)}</div>}{group.note && <small>{group.note}</small>}</fieldset>)}
    {(dish.raita_available ?? dish.category === 'Biryani') && <label className="check raita-option"><input type="checkbox" aria-label={`Extra raita for ${dish.name}`} checked={addon} onChange={e => onChange(portion, e.target.checked, selections)} /><span>Extra raita <small>Contains milk</small></span><strong>+₹30</strong></label>}
    {!!dish.customizations?.length && <small className="preference-note">Preparation preferences have no extra charge. They do not remove allergens from the recipe.</small>}
  </div>;
}
