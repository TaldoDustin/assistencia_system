import { getStatusColor } from "@/lib/constants";

export default function OrderStatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(status)}`}>
      {status || "—"}
    </span>
  );
}
