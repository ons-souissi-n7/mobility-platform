"use server";

import { revalidateTag } from "next/cache";

export async function revalidateDepartments() {
  revalidateTag("ref-departments", {});
}

export async function revalidateLevels() {
  revalidateTag("ref-levels", {});
}

export async function revalidateUniversities() {
  revalidateTag("ref-partner-universities", {});
}

export async function revalidateParcours() {
  revalidateTag("ref-parcours", {});
}
