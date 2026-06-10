import * as SelectPrimitive from "@radix-ui/react-select"; import { ChevronDown, ChevronUp, Check } from "lucide-react";

/*  Emergency minimal Select wrapper to unblock build.  Reintroduce full implementation after deploy succeeds. */ export const Select =
SelectPrimitive.Root; export const SelectGroup = SelectPrimitive.Group; export const SelectValue = SelectPrimitive.Value;

export function SelectTrigger(props) {  return (  <SelectPrimitive.Trigger {...props}>  {props.children}  <SelectPrimitive.Icon asChild>  
<ChevronDown />  </SelectPrimitive.Icon>  </SelectPrimitive.Trigger>  ); }

export function SelectContent(props) {  return (  <SelectPrimitive.Portal>  <SelectPrimitive.Content {...props}> 
<SelectPrimitive.ScrollUpButton><ChevronUp /></SelectPrimitive.ScrollUpButton> 
<SelectPrimitive.Viewport>{props.children}</SelectPrimitive.Viewport>  <SelectPrimitive.ScrollDownButton><ChevronDown />
</SelectPrimitive.ScrollDownButton>  </SelectPrimitive.Content>  </SelectPrimitive.Portal>  ); }

export function SelectItem({ children, ...props }) {  // keep minimal and safe  if (props && props.value === "") return null;  return ( 
<SelectPrimitive.Item {...props}>  <SelectPrimitive.ItemIndicator><Check /></SelectPrimitive.ItemIndicator> 
<SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>  </SelectPrimitive.Item>  ); }

export function SelectLabel(props) {  return <SelectPrimitive.Label {...props} />; } export function SelectSeparator(props) {  return
<SelectPrimitive.Separator {...props} />; }
