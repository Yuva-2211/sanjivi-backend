import { appendFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";
import nodemailer from "nodemailer";
import { createClient } from "@supabase/supabase-js";

export const runtime = "nodejs";

const EMAIL_RECIPIENT = process.env.EARLY_ACCESS_EMAIL_RECIPIENT ?? "sanjivi.ai.care@zohomail.in";
const SMTP_HOST = process.env.SMTP_HOST;
const SMTP_PORT = process.env.SMTP_PORT ? Number(process.env.SMTP_PORT) : undefined;
const SMTP_USER = process.env.SMTP_USER;
const SMTP_PASS = process.env.SMTP_PASS;
const SMTP_FROM = process.env.SMTP_FROM ?? SMTP_USER ?? "no-reply@sanjivi.ai";
const SEND_CONFIRMATION_EMAIL = process.env.EARLY_ACCESS_SEND_CONFIRMATION_EMAIL?.toLowerCase() === "true";

const supabase = process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY
  ? createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY)
  : null;

function createTransporter() {
  return nodemailer.createTransport({
    host: SMTP_HOST,
    port: SMTP_PORT,
    secure: SMTP_PORT === 465,
    auth: {
      user: SMTP_USER,
      pass: SMTP_PASS,
    },
  });
}

async function sendNotificationEmail(name: string, email: string) {
  if (!SMTP_HOST || !SMTP_PORT || !SMTP_USER || !SMTP_PASS) {
    return null;
  }

  const transporter = createTransporter();

  return transporter.sendMail({
    from: SMTP_FROM,
    to: EMAIL_RECIPIENT,
    subject: "New Early Access Signup",
    text: `New early access signup received.\n\nName: ${name}\nEmail: ${email}\nReceived: ${new Date().toISOString()}\n`,
    html: `<p>A new early access signup was received.</p><ul><li><strong>Name:</strong> ${name}</li><li><strong>Email:</strong> ${email}</li><li><strong>Received:</strong> ${new Date().toISOString()}</li></ul>`,
  });
}

async function sendSubscriberConfirmation(name: string, email: string) {
  if (!SEND_CONFIRMATION_EMAIL || !SMTP_HOST || !SMTP_PORT || !SMTP_USER || !SMTP_PASS) {
    return null;
  }

  const transporter = createTransporter();

  return transporter.sendMail({
    from: SMTP_FROM,
    to: email,
    subject: "Thanks for joining Sanjivi AI early access",
    text: `Hi ${name},\n\nThank you for joining the Sanjivi AI early access list. We have received your request and will notify you when access is ready.\n\nBest regards,\nThe Sanjivi AI team`,
    html: `<p>Hi ${name},</p><p>Thank you for joining the Sanjivi AI early access list. We have received your request and will notify you when access is ready.</p><p>Best regards,<br/>The Sanjivi AI team</p>`,
  });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const name = String(body?.name || "").trim();
  const email = String(body?.email || "").trim().toLowerCase();

  if (!name || !email) {
    return NextResponse.json({ error: "Name and email are required." }, { status: 400 });
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: "Enter a valid email address." }, { status: 400 });
  }

  try {
    if (supabase) {
      const { error } = await supabase
        .from("early_access_signups")
        .insert([{ name, email, created_at: new Date().toISOString() }]);
      if (error) {
        // Postgres unique-violation — duplicate email
        if (error.code === "23505") {
          return NextResponse.json(
            { ok: true, message: "You are already on the early access list — we will be in touch!" },
            { status: 200 },
          );
        }
        throw error;
      }
    } else {
      const dataDir = path.join(process.cwd(), "data");
      const filePath = path.join(dataDir, "early-access-signups.jsonl");
      await mkdir(dataDir, { recursive: true });
      await appendFile(
        filePath,
        `${JSON.stringify({ name, email, createdAt: new Date().toISOString() })}\n`,
        "utf8",
      );
    }
  } catch (error) {
    console.error("Storage error:", error);
    return NextResponse.json({ error: "Unable to save your signup right now. Please try again shortly." }, { status: 500 });
  }

  if (SMTP_HOST && SMTP_PORT && SMTP_USER && SMTP_PASS) {
    // Fire-and-forget — a failed email must not invalidate a successful signup
    Promise.all([
      sendNotificationEmail(name, email),
      sendSubscriberConfirmation(name, email),
    ]).catch((err) => console.error("Early access notification failed:", err));
  }

  return NextResponse.json({
    ok: true,
    message: "Thanks! You are on the early access list — we will notify you when access is ready.",
  });
}
