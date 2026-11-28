// safe-commands.js
// Add-on commands for an EXISTING Baileys WhatsApp socket.
// This file does NOT create a WhatsApp connection or touch your session.

const PREFIX = '.';

function getText(m) {
  const msg = m.message || {};
  return (
    msg.conversation ||
    msg.extendedTextMessage?.text ||
    msg.imageMessage?.caption ||
    msg.videoMessage?.caption ||
    msg.documentMessage?.caption ||
    ''
  ).trim();
}

async function reply(sock, m, text) {
  return sock.sendMessage(m.key.remoteJid, { text }, { quoted: m });
}

async function isGroupAdmin(sock, m) {
  const jid = m.key.remoteJid;
  if (!jid.endsWith('@g.us')) return false;
  const meta = await sock.groupMetadata(jid);
  const sender = m.key.participant || m.key.remoteJid;
  const participant = meta.participants.find(p => p.id === sender);
  return Boolean(participant?.admin);
}

async function handleCommand(sock, m) {
  const chat = m.key.remoteJid;
  const body = getText(m);
  if (!body.startsWith(PREFIX)) return false;

  const [rawCommand, ...args] = body.slice(PREFIX.length).split(/\s+/);
  const command = (rawCommand || '').toLowerCase();

  try {
    switch (command) {
      case 'ping': {
        const start = Date.now();
        await reply(sock, m, `🏓 Pong!\nResponse: ${Date.now() - start} ms`);
        return true;
      }

      case 'help':
      case 'menu': {
        await reply(sock, m,
`🤖 *BOT COMMANDS*

GENERAL
.ping — Check bot response
.help — Show this menu

GROUP ADMIN (admins only)
.promote @user — Make a member an admin
.demote @user — Remove admin status
.invitelink — Get this group's invite link
.gleave — Make the bot leave this group

Use these commands in the group where you want the action.`);
        return true;
      }

      case 'promote':
      case 'demote': {
        if (!chat.endsWith('@g.us')) {
          await reply(sock, m, 'This command only works in a group.');
          return true;
        }
        if (!(await isGroupAdmin(sock, m))) {
          await reply(sock, m, 'Only group admins can use this command.');
          return true;
        }

        const mentioned = m.message?.extendedTextMessage?.contextInfo?.mentionedJid || [];
        const quotedParticipant = m.message?.extendedTextMessage?.contextInfo?.participant;
        const target = mentioned[0] || quotedParticipant;
        if (!target) {
          await reply(sock, m, `Tag a member or reply to their message.\nExample: .${command} @user`);
          return true;
        }

        await sock.groupParticipantsUpdate(
          chat,
          [target],
          command === 'promote' ? 'promote' : 'demote'
        );
        await reply(sock, m, command === 'promote' ? '✅ Member promoted.' : '✅ Admin demoted.');
        return true;
      }

      case 'invitelink': {
        if (!chat.endsWith('@g.us')) {
          await reply(sock, m, 'Use this command inside a group.');
          return true;
        }
        if (!(await isGroupAdmin(sock, m))) {
          await reply(sock, m, 'Only group admins can request the invite link.');
          return true;
        }
        const code = await sock.groupInviteCode(chat);
        await reply(sock, m, `🔗 Group invite link:\nhttps://chat.whatsapp.com/${code}`);
        return true;
      }

      case 'gleave': {
        if (!chat.endsWith('@g.us')) {
          await reply(sock, m, 'Use this command inside the group the bot should leave.');
          return true;
        }
        // Only the bot owner should be allowed to make the bot leave.
        const ownerJid = (process.env.BOT_OWNER_NUMBER || '').replace(/\D/g, '') + '@s.whatsapp.net';
        const sender = m.key.participant || '';
        if (!process.env.BOT_OWNER_NUMBER || sender !== ownerJid) {
          await reply(sock, m, 'Only the configured bot owner can use .gleave.');
          return true;
        }
        await reply(sock, m, 'I am leaving this group now.');
        await sock.groupLeave(chat);
        return true;
      }

      default:
        return false;
    }
  } catch (err) {
    console.error('[safe-commands]', err);
    await reply(sock, m, `❌ Command failed: ${err.message || 'unknown error'}`);
    return true;
  }
}

module.exports = { handleCommand, getText };
