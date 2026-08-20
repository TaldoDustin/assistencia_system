import { Badge } from "@/components/ui/badge";
import { getStatusVariant } from "@/lib/constants";

export default function OrderStatusBadge({ status }) {
  return <Badge variant={getStatusVariant(status)}>{status || "—"}</Badge>;
}
