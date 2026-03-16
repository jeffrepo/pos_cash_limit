/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate = false) {
        const order = this.currentOrder;
        const efectivoMaximo = Number(this.pos.config.efectivo_maximo || 0);
        const sesionId =
            order?.session_id?.id ||
            order?.session_id ||
            this.pos?.session?.id ||
            this.pos?.pos_session?.id;

        let pagoEfectivo = false;
        let ventaEfectivoActual = 0;
        const cambio = Math.abs(Number(order.change || 0));

        for (const line of order.payment_ids || []) {
            const method = line.payment_method_id;
            if (!method) {
                continue;
            }
            if (method.type === "cash") {
                pagoEfectivo = true;
                ventaEfectivoActual += Number(line.amount || 0);
            }
        }

        if (!pagoEfectivo && (order.payment_ids?.length || 0) >= 1 && cambio > 0) {
            this.dialog.add(AlertDialog, {
                title: _t("Error en pago"),
                body: _t("Monto de pago incorrecto"),
            });
            return;
        }

        console.log("efectivoMaximo", efectivoMaximo);
        console.log("sesionId", sesionId);
        console.log("ventaEfectivoActual", ventaEfectivoActual);

        if (!sesionId || !efectivoMaximo) {
            return await super.validateOrder(isForceValidate);
        }

        let sesion = [];
        try {
            sesion = await this.pos.data.call(
                "pos.session",
                "search_read",
                [[["id", "=", sesionId]], ["pagos_efectivo", "retiros_efectivo"]]
            );
        } catch (error) {
            console.error("Error consultando sesión POS", error);
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("No se pudo consultar la sesión actual."),
            });
            return;
        }

        console.log("sesion", sesion);

        if (!sesion || !sesion.length) {
            return await super.validateOrder(isForceValidate);
        }

        const pagosEfectivo = Number(sesion[0].pagos_efectivo || 0);
        const retirosEfectivo = Number(sesion[0].retiros_efectivo || 0);
        const totalEfectivo = pagosEfectivo + ventaEfectivoActual - retirosEfectivo;

        console.log("pagosEfectivo", pagosEfectivo);
        console.log("retirosEfectivo", retirosEfectivo);
        console.log("totalEfectivo", totalEfectivo);

        if (totalEfectivo >= efectivoMaximo) {
            this.dialog.add(AlertDialog, {
                title: _t("Límite de efectivo"),
                body: _t("Se alcanzó el efectivo máximo permitido en caja."),
            });
            return;
        }

        return await super.validateOrder(isForceValidate);
    },
});